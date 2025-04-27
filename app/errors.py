from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from flask_jwt_extended.exceptions import JWTExtendedException
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
import traceback
import sentry_sdk

def error_response(status_code, message=None):
    """Generate error response with consistent format"""
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return error_response(400, str(error))
    
    @app.errorhandler(401)
    def unauthorized(error):
        return error_response(401, 'Authentication required')
    
    @app.errorhandler(403)
    def forbidden(error):
        return error_response(403, 'Insufficient permissions')
    
    @app.errorhandler(404)
    def not_found(error):
        return error_response(404, 'Resource not found')
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(405, 'Method not allowed')
    
    @app.errorhandler(429)
    def too_many_requests(error):
        return error_response(429, 'Too many requests')
    
    @app.errorhandler(500)
    def internal_server_error(error):
        # Log the error
        app.logger.error(f'Server Error: {str(error)}')
        app.logger.error(traceback.format_exc())
        
        # Send to Sentry if configured
        if sentry_sdk.Hub.current.client:
            sentry_sdk.capture_exception(error)
        
        return error_response(500, 'Internal server error')
    
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(error):
        return error_response(401, str(error))
    
    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        # Log the error
        app.logger.error(f'Database Error: {str(error)}')
        app.logger.error(traceback.format_exc())
        
        # Send to Sentry if configured
        if sentry_sdk.Hub.current.client:
            sentry_sdk.capture_exception(error)
        
        return error_response(500, 'Database error occurred')
    
    @app.errorhandler(RedisError)
    def handle_redis_error(error):
        # Log the error
        app.logger.error(f'Redis Error: {str(error)}')
        app.logger.error(traceback.format_exc())
        
        # Send to Sentry if configured
        if sentry_sdk.Hub.current.client:
            sentry_sdk.capture_exception(error)
        
        return error_response(500, 'Cache error occurred')
