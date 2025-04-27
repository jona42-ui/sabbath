from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app import db, limiter
from app.utils.email import send_verification_email, send_reset_password_email
from app.utils.validators import validate_password, validate_email
from app.utils.decorators import verify_recaptcha
from .models import (
    login_model, register_model, user_model,
    success_response, error_response
)

auth_ns = Namespace(
    'auth',
    description='Authentication and user management operations',
    decorators=[limiter.limit("10/minute")]
)

# Register models
auth_ns.models[login_model.name] = login_model
auth_ns.models[register_model.name] = register_model
auth_ns.models[user_model.name] = user_model
auth_ns.models[success_response.name] = success_response
auth_ns.models[error_response.name] = error_response

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('register_user')
    @auth_ns.expect(register_model)
    @auth_ns.response(201, 'User registered successfully', success_response)
    @auth_ns.response(400, 'Validation error', error_response)
    @auth_ns.response(409, 'User already exists', error_response)
    @verify_recaptcha
    def post(self):
        """Register a new user"""
        data = request.get_json()
        
        # Validate input
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate email and password
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        password_validation = validate_password(data['password'])
        if password_validation is not True:
            return jsonify({'error': password_validation}), 400
        
        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.password = data['password']
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            send_verification_email(user)
            
            return jsonify({
                'message': 'Registration successful. Please check your email to verify your account.',
                'user': user.to_dict()
            }), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            return jsonify({'error': 'Registration failed'}), 500

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login_user')
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful', success_response)
    @auth_ns.response(401, 'Invalid credentials', error_response)
    def post(self):
        """Login user and return JWT tokens"""
        data = request.get_json()
        
        if not all(k in data for k in ('username', 'password')):
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.verify_password(data['password']):
            if not user.email_verified:
                return jsonify({
                    'error': 'Please verify your email before logging in',
                    'email_verified': False
                }), 401
            
            if not user.active:
                return jsonify({'error': 'Account is deactivated'}), 401
            
            # Update last seen
            user.update_last_seen()
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }), 200
        
        return jsonify({'error': 'Invalid username or password'}), 401

@auth_ns.route('/refresh')
class TokenRefresh(Resource):
    @auth_ns.doc('refresh_token')
    @auth_ns.response(200, 'Token refreshed', success_response)
    @auth_ns.response(401, 'Invalid refresh token', error_response)
    @jwt_required(refresh=True)
    def post(self):
        """Refresh access token"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        return jsonify({'access_token': access_token}), 200

@auth_ns.route('/verify-email/<token>')
class EmailVerification(Resource):
    @auth_ns.doc('verify_email')
    @auth_ns.response(200, 'Email verified', success_response)
    @auth_ns.response(400, 'Invalid token', error_response)
    def get(self, token):
        """Verify user's email address"""
        try:
            user_id = User.verify_email_token(token)
            if not user_id:
                return jsonify({'error': 'Invalid or expired verification token'}), 400
            
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.email_verified:
                return jsonify({'message': 'Email already verified'}), 200
            
            user.email_verified = True
            db.session.commit()
            
            return jsonify({'message': 'Email verified successfully'}), 200
        except Exception as e:
            current_app.logger.error(f"Email verification error: {str(e)}")
            return jsonify({'error': 'Verification failed'}), 500

@auth_ns.route('/forgot-password')
class ForgotPassword(Resource):
    @auth_ns.doc('forgot_password')
    @auth_ns.response(200, 'Reset email sent', success_response)
    @auth_ns.response(400, 'Invalid email', error_response)
    def post(self):
        """Send password reset email"""
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                send_reset_password_email(user)
                return jsonify({
                    'message': 'Password reset instructions sent to your email'
                }), 200
            except Exception as e:
                current_app.logger.error(f"Password reset email error: {str(e)}")
                return jsonify({'error': 'Failed to send reset email'}), 500
        
        # Return success even if email not found to prevent email enumeration
        return jsonify({
            'message': 'If this email is registered, you will receive reset instructions'
        }), 200

@auth_ns.route('/reset-password/<token>')
class ResetPassword(Resource):
    @auth_ns.doc('reset_password')
    @auth_ns.response(200, 'Password reset successful', success_response)
    @auth_ns.response(400, 'Invalid token or password', error_response)
    def post(self, token):
        """Reset user's password"""
        try:
            user = User.verify_reset_password_token(token)
            if not user:
                return jsonify({'error': 'Invalid or expired reset token'}), 400
            
            data = request.get_json()
            password = data.get('password')
            
            if not password:
                return jsonify({'error': 'New password is required'}), 400
            
            password_validation = validate_password(password)
            if password_validation is not True:
                return jsonify({'error': password_validation}), 400
            
            user.password = password
            db.session.commit()
            
            return jsonify({'message': 'Password reset successful'}), 200
        except Exception as e:
            current_app.logger.error(f"Password reset error: {str(e)}")
            return jsonify({'error': 'Password reset failed'}), 500

@auth_ns.route('/change-password')
class ChangePassword(Resource):
    @auth_ns.doc('change_password')
    @auth_ns.response(200, 'Password changed', success_response)
    @auth_ns.response(401, 'Invalid current password', error_response)
    @jwt_required()
    def post(self):
        """Change user's password"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        data = request.get_json()
        if not all(k in data for k in ('current_password', 'new_password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not user.verify_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        password_validation = validate_password(data['new_password'])
        if password_validation is not True:
            return jsonify({'error': password_validation}), 400
        
        try:
            user.password = data['new_password']
            db.session.commit()
            return jsonify({'message': 'Password changed successfully'}), 200
        except Exception as e:
            current_app.logger.error(f"Password change error: {str(e)}")
            return jsonify({'error': 'Password change failed'}), 500
