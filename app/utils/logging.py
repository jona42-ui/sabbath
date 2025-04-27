import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask import has_request_context, request
import json
from datetime import datetime

class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request details"""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.method = request.method
            record.ip = request.remote_addr
            record.user_agent = request.user_agent.string
            record.correlation_id = request.headers.get('X-Correlation-ID', '')
        else:
            record.url = None
            record.method = None
            record.ip = None
            record.user_agent = None
            record.correlation_id = None
            
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_keys = [
            'name', 'levelname', 'message', 'asctime'
        ]
    
    def format(self, record):
        message = {
            'timestamp': datetime.utcnow().isoformat(),
            'logger': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
        }
        
        if hasattr(record, 'props'):
            message.update(record.props)
        
        if has_request_context():
            message.update({
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string,
                'correlation_id': request.headers.get('X-Correlation-ID', '')
            })
        
        if record.exc_info:
            message['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(message)

def setup_logging(app):
    """Configure application logging"""
    
    # Set basic logging config
    logging.basicConfig(level=logging.INFO)
    
    if not app.debug and not app.testing:
        # File handler
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Regular log file
        file_handler = RotatingFileHandler(
            'logs/sabbath.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(RequestFormatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d] '
            'url: %(url)s method: %(method)s ip: %(ip)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # JSON log file for ELK/monitoring
        json_handler = RotatingFileHandler(
            'logs/sabbath.json.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.INFO)
        app.logger.addHandler(json_handler)
        
        # Email error notifications
        if app.config.get('MAIL_SERVER'):
            auth = None
            if app.config.get('MAIL_USERNAME') or app.config.get('MAIL_PASSWORD'):
                auth = (app.config.get('MAIL_USERNAME'),
                       app.config.get('MAIL_PASSWORD'))
            secure = None
            if app.config.get('MAIL_USE_TLS'):
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config.get('MAIL_SERVER'),
                         app.config.get('MAIL_PORT')),
                fromaddr=app.config.get('MAIL_DEFAULT_SENDER'),
                toaddrs=app.config.get('ADMINS'),
                subject='Sabbath Application Error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        
        # Log application startup
        app.logger.info('Sabbath application startup')
