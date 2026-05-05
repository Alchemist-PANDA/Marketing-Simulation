import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app

client = TestClient(app)

def test_health():
    """Test both canonical and alias health endpoints"""
    for endpoint in ["/health", "/api/health"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "version": "1.0.0"}

def test_simulate_happy_path():
    """Test successful simulation with all fields"""
    payload = {
        "text": "Get 50% off today! Limited offer.",
        "price": 19.99,
        "category": "fashion",
        "social_proof": 4.5,
        "urgency": 4.0,
        "channel": "facebook",
        "agents": 500,
        "seed": 42
    }
    for endpoint in ["/simulate", "/api/simulate"]:
        response = client.post(endpoint, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predicted_ctr" in data
        assert "predicted_cvr" in data
        assert "confidence_score" in data
        assert "raw_metrics" in data
        assert "failure_reasons" in data
        assert data["raw_metrics"]["conversions"] >= 0

def test_simulate_validation_errors():
    """Test that invalid inputs return 422"""
    invalid_payloads = [
        {"text": "", "channel": "facebook"}, # empty text
        {"text": "hi", "channel": "invalid_channel"}, # bad channel
        {"text": "hi", "agents": 50}, # agents too low
        {"text": "hi", "price": -10}, # negative price
        {"text": "hi", "social_proof": 6}, # social_proof too high
    ]
    for payload in invalid_payloads:
        response = client.post("/simulate", json=payload)
        assert response.status_code == 422

def test_determinism():
    """Test that same seed gives same results"""
    payload = {
        "text": "Limited time offer!",
        "agents": 500,
        "seed": 123
    }
    response1 = client.post("/simulate", json=payload)
    response2 = client.post("/simulate", json=payload)

    assert response1.json() == response2.json()

def test_calibrate():
    """Test calibration endpoint"""
    payload = {
        "predicted_ctr": 0.05,
        "actual_ctr": 0.04,
        "predicted_cvr": 0.10,
        "actual_cvr": 0.08
    }
    for endpoint in ["/calibrate", "/api/calibrate"]:
        response = client.post(endpoint, json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "calibrator updated"

def test_ab_test_logic():
    """Test ABTestRunner logic (indirectly via MaxSimulation if needed or unit test)"""
    from src.simulation.ab_test_runner import ABTestRunner
    runner = ABTestRunner(num_agents=100, seed=42)
    result = runner.run_test("Ad A", "Ad B", objective="conversions")
    assert "winner" in result
    assert "lift_percentage" in result
    assert result["objective"] == "conversions"
