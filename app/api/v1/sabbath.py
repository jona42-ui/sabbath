from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app import db, limiter
from app.utils.monitoring import track_resource_usage
from app.utils.sabbath import calculate_sabbath_times
from datetime import datetime, timedelta
from .models import (
    sabbath_times, preparation_checklist,
    success_response, error_response
)

sabbath_ns = Namespace(
    'sabbath',
    description='Sabbath times and preparation management',
    decorators=[jwt_required()]
)

# Register models
sabbath_ns.models[sabbath_times.name] = sabbath_times
sabbath_ns.models[preparation_checklist.name] = preparation_checklist
sabbath_ns.models[success_response.name] = success_response
sabbath_ns.models[error_response.name] = error_response

@sabbath_ns.route('/times')
class SabbathTimes(Resource):
    @sabbath_ns.doc('get_sabbath_times')
    @sabbath_ns.param('date', 'Date (YYYY-MM-DD), defaults to next Sabbath')
    @sabbath_ns.param('latitude', 'Location latitude')
    @sabbath_ns.param('longitude', 'Location longitude')
    @sabbath_ns.response(200, 'Success', model=sabbath_times)
    @track_resource_usage('get_sabbath_times')
    def get(self):
        """Get Sabbath times for a specific date and location"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Get parameters
        date_str = request.args.get('date')
        lat = request.args.get('latitude', type=float)
        lon = request.args.get('longitude', type=float)
        
        try:
            # If no date provided, get next Sabbath
            if not date_str:
                today = datetime.utcnow().date()
                days_until_sabbath = (5 - today.weekday()) % 7
                date = today + timedelta(days=days_until_sabbath)
            else:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Use user's default location if not provided
            if lat is None or lon is None:
                profile = user.profile or {}
                location = profile.get('location', {})
                lat = location.get('latitude')
                lon = location.get('longitude')
                
                if lat is None or lon is None:
                    return jsonify({
                        'error': 'Location coordinates required'
                    }), 400
            
            # Calculate times
            times = calculate_sabbath_times(date, lat, lon, user.timezone)
            
            return jsonify(times), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"Sabbath times calculation error: {str(e)}")
            return jsonify({'error': 'Failed to calculate Sabbath times'}), 500

@sabbath_ns.route('/preparation-checklist')
class PreparationChecklist(Resource):
    @sabbath_ns.doc('get_preparation_checklist')
    @sabbath_ns.response(200, 'Success', model=preparation_checklist)
    @track_resource_usage('get_preparation_checklist')
    def get(self):
        """Get personalized Sabbath preparation checklist"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        try:
            # Get user preferences
            profile = user.profile or {}
            preferences = profile.get('sabbath_preferences', {})
            
            # Build checklist based on preferences
            checklist = {
                'spiritual': [
                    'Review the week\'s blessings and answered prayers',
                    'Study the Sabbath School lesson',
                    'Prepare special Bible readings or devotionals',
                    'Set aside time for family worship'
                ],
                'physical': [
                    'Clean and tidy the home',
                    'Prepare Sabbath meals in advance',
                    'Set out Sabbath clothes',
                    'Personal grooming and preparation'
                ],
                'service': [
                    'Prepare materials for church responsibilities',
                    'Plan acts of service or visitation',
                    'Coordinate with church family as needed'
                ],
                'custom': preferences.get('custom_tasks', [])
            }
            
            # Add preference-specific tasks
            if preferences.get('meal_prep'):
                checklist['physical'].extend([
                    'Plan Sabbath meals',
                    'Grocery shopping',
                    'Cook and prepare food'
                ])
            
            if preferences.get('family_worship'):
                checklist['spiritual'].extend([
                    'Choose worship songs',
                    'Prepare family discussion topics',
                    'Set up worship space'
                ])
            
            if preferences.get('outreach'):
                checklist['service'].extend([
                    'Prepare outreach materials',
                    'Contact potential visitors',
                    'Arrange transportation if needed'
                ])
            
            return jsonify(checklist), 200
            
        except Exception as e:
            current_app.logger.error(f"Checklist generation error: {str(e)}")
            return jsonify({'error': 'Failed to generate checklist'}), 500

@sabbath_ns.route('/preferences')
class SabbathPreferences(Resource):
    @sabbath_ns.doc('get_preferences')
    @sabbath_ns.response(200, 'Success', success_response)
    def get(self):
        """Get user's Sabbath preferences"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        profile = user.profile or {}
        preferences = profile.get('sabbath_preferences', {})
        
        return jsonify({
            'preferences': preferences
        }), 200
    
    @sabbath_ns.doc('update_preferences')
    @sabbath_ns.response(200, 'Preferences updated', success_response)
    @sabbath_ns.response(400, 'Invalid preferences', error_response)
    def put(self):
        """Update user's Sabbath preferences"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        data = request.get_json()
        
        try:
            profile = user.profile or {}
            profile['sabbath_preferences'] = data
            user.profile = profile
            
            db.session.commit()
            
            return jsonify({
                'message': 'Preferences updated successfully',
                'preferences': data
            }), 200
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Preferences update error: {str(e)}")
            return jsonify({'error': 'Failed to update preferences'}), 500
