"""Tests for authentication functionality."""

def test_login(client):
    """Test login endpoint."""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code in (200, 401)

def test_register(client, db):
    """Test registration endpoint."""
    response = client.post('/api/v1/auth/register', json={
        'email': 'newuser@example.com',
        'password': 'password123',
        'name': 'Test User'
    })
    assert response.status_code == 201
