import pytest
from api_server import create_app
import json

@pytest.fixture
def app(test_db):
    """Create a test Flask app"""
    app = create_app(test_db)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'

def test_get_group_words(client):
    """Test getting words for a group"""
    # Test existing group
    response = client.get('/api/groups/1/raw')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['kanji'] == '猫'
    assert data[1]['kanji'] == '犬'

    # Test non-existent group
    response = client.get('/api/groups/999/raw')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 0

def test_invalid_group_id(client):
    """Test invalid group ID handling"""
    response = client.get('/api/groups/invalid/raw')
    assert response.status_code == 404 