"""Test configuration and fixtures."""

import pytest
from app import create_app
from app.models import db as _db

@pytest.fixture
def app():
    """Create application for the tests."""
    _app = create_app('testing')
    _app.config['TESTING'] = True
    return _app

@pytest.fixture
def db(app):
    """Create database for the tests."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.close()
        _db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()
