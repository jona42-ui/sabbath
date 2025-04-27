"""Tests for spiritual growth functionality."""

import pytest
from app.models import User

@pytest.fixture
def auth_headers(client, db):
    """Create authenticated user and return auth headers."""
    # Create test user
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # Get auth token
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_spiritual_progress(client, auth_headers):
    """Test spiritual progress tracking."""
    response = client.post('/api/v1/spiritual/progress', json={
        'category': 'bible_study',
        'progress': 75,
        'notes': 'Completed daily reading'
    }, headers=auth_headers)
    assert response.status_code == 201

def test_spiritual_stats(client, auth_headers):
    """Test spiritual stats retrieval."""
    response = client.get('/api/v1/spiritual/stats', headers=auth_headers)
    assert response.status_code == 200
    assert 'bible_study' in response.json
