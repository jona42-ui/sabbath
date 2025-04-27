from flask import Blueprint
from flask_restx import Api
from .auth import auth_ns
from .spiritual import spiritual_ns
from .sabbath import sabbath_ns

# Create Blueprint
api_v1 = Blueprint('api_v1', __name__)

# Initialize API with Swagger documentation
api = Api(
    api_v1,
    title='Sabbath API',
    version='1.0',
    description='API for Sabbath time tracking and spiritual growth management',
    doc='/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Type in the *\'Value\'* input box below: **\'Bearer &lt;JWT&gt;\'**, where JWT is the token'
        }
    },
    security='Bearer'
)

# Register namespaces
api.add_namespace(auth_ns, path='/auth')
api.add_namespace(spiritual_ns, path='/spiritual')
api.add_namespace(sabbath_ns, path='/sabbath')
