"""Configuration settings for the Sabbath Companion application."""

import os
from datetime import timedelta

class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///sabbath.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    
    # API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    HEBCAL_API_KEY = os.environ.get('HEBCAL_API_KEY')
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Monitoring
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    ELASTIC_APM = {
        'SERVICE_NAME': 'sabbath-companion',
        'SERVER_URL': os.environ.get('ELASTIC_APM_SERVER_URL'),
    }

class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    DEVELOPMENT = True

class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    DEVELOPMENT = False
    
    # Production should always use strong secret keys
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("No SECRET_KEY set for production environment")
        return key
    
    @property
    def JWT_SECRET_KEY(self):
        key = os.environ.get('JWT_SECRET_KEY')
        if not key:
            raise ValueError("No JWT_SECRET_KEY set for production environment")
        return key

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
