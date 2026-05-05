import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_me_endpoint_local_mode(monkeypatch):
    """Verify /api/me returns local user when no Supabase credentials."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    response = client.get("/api/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "00000000-0000-0000-0000-000000000000"
    assert data["email"] == "dev@local.host"
    assert data["mode"] == "local"
    assert data["is_authenticated"] is True

def test_me_endpoint_supabase_no_token(monkeypatch):
    """Verify /api/me returns 401 when Supabase enabled but no token."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")

    response = client.get("/api/me")
    assert response.status_code == 401
    assert "Missing or invalid Authorization header" in response.json()["detail"]

def test_me_endpoint_supabase_invalid_token(monkeypatch):
    """Verify /api/me returns 401 when Supabase enabled with invalid token."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")

    response = client.get("/api/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]

def test_me_endpoint_supabase_malformed_header(monkeypatch):
    """Verify /api/me returns 401 with malformed Authorization header."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")

    response = client.get("/api/me", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == 401
    assert "Missing or invalid Authorization header" in response.json()["detail"]

def test_health_unprotected(monkeypatch):
    """Verify /health works without auth in both modes."""
    # Test in local mode
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # Test in Supabase mode
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_simulate_unprotected(monkeypatch):
    """Verify /simulate works without auth in both modes."""
    payload = {
        "text": "Test ad",
        "price": 20.0,
        "category": "general",
        "social_proof": 3.0,
        "urgency": 2.5,
        "channel": "facebook",
        "agents": 100,
        "seed": 42
    }

    # Test in local mode
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    assert "predicted_ctr" in response.json()

    # Test in Supabase mode
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    assert "predicted_ctr" in response.json()
