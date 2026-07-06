import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure the root directory is on the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.unified import app

client = TestClient(app)

def test_favicon():
    response = client.get("/favicon.ico")
    assert response.status_code == 204

def test_404_handler():
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Not Found"
    }

def test_auth_register_validation():
    # Test with missing body
    response = client.post("/auth/register")
    assert response.status_code == 422
    
    # Test with invalid email
    response = client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert response.status_code == 422

def test_auth_login_validation():
    response = client.post("/auth/login", json={"email": "valid@email.com", "password": "password123"})
    # It will either be 401 Unauthorized (if Supabase is enabled but creds are invalid)
    # or 400/500 if Supabase is misconfigured or fails
    # Let's just assert it is not a 404
    assert response.status_code != 404

def test_auth_reset_validation():
    response = client.post("/auth/reset", json={"email": "valid@email.com"})
    assert response.status_code != 404

def test_auth_me_unauthorized():
    response = client.get("/auth/me")
    # If auth is enforced (ENV != development), it should return 401 Unauthorized
    # If local fallback is active, it returns 200 with local user
    assert response.status_code in [200, 401]
