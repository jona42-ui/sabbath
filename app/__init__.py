from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from elasticapm.contrib.flask import ElasticAPM
from dotenv import load_dotenv
import os
import redis

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
apm = ElasticAPM()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name='default'):
    """Create Flask application.
    
    Args:
        config_name: Name of configuration to use
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    
    # Security headers
    from flask_talisman import Talisman
    Talisman(app, 
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", 'data:', 'https:'],
            'font-src': ["'self'", 'https:', 'data:'],
            'connect-src': ["'self'", 'https://api.openai.com']
        },
        force_https=True
    )
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={
        r"/api/*": {"origins": os.getenv("ALLOWED_ORIGINS", "*").split(",")}
    })
    
    # Configure Redis
    app.redis = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    
    if app.config.get('ELASTIC_APM', {}).get('SERVER_URL'):
        apm.init_app(app)
    
    # Register blueprints
    from app.api.v1 import api_v1
    from app.auth import auth
    from app.main import main
    app.register_blueprint(api_v1, url_prefix='/api/v1')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main)
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Register CLI commands
    from app.commands import register_commands
    register_commands(app)
    
    return app
