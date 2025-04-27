"""WSGI entry point for the Sabbath Companion application."""

import os
from app import create_app

# Create the Flask application instance
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run()
