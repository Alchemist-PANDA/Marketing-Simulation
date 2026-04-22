import pytest
import requests
import json
import os
import sys

# Add src to path for potential unit testing of API logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def api_base_url():
    return "http://localhost:8000"

@pytest.fixture
def sample_payload():
    return {
        "campaign_id": "CMP-001",
        "segment": "Tech Enthusiasts",
        "budget": 1000,
        "duration_days": 7,
        "objective": "conversion_rate"
    }

def test_api_is_running(api_base_url):
    """
    Test that the FastAPI server is reachable.
    Note: Requires server to be running (make dashboard).
    """
    try:
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    except requests.exceptions.ConnectionError:
        pytest.skip("❌ API server is not running at " + api_base_url)

def test_get_campaign_details(api_base_url):
    """
    Test getting details for an existing campaign.
    """
    try:
        response = requests.get(f"{api_base_url}/api/campaigns/CMP-001")
        if response.status_code == 404:
             pytest.skip("⚠️ Campaign CMP-001 not found in current session")
        assert response.status_code == 200
        assert "campaign_id" in response.json()
    except requests.exceptions.ConnectionError:
        pytest.skip("❌ API server is not running")

def test_create_simulation_request(api_base_url, sample_payload):
    """
    Test creating a new simulation via the API.
    """
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{api_base_url}/api/simulate",
            data=json.dumps(sample_payload),
            headers=headers
        )
        # We expect 202 (Accepted) for long-running simulations
        assert response.status_code in [200, 201, 202]
        assert "job_id" in response.json()
    except requests.exceptions.ConnectionError:
        pytest.skip("❌ API server is not running")

def test_get_reports_list(api_base_url):
    """
    Test fetching the list of available reports.
    """
    try:
        response = requests.get(f"{api_base_url}/api/reports")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    except requests.exceptions.ConnectionError:
        pytest.skip("❌ API server is not running")

def test_error_handling_invalid_id(api_base_url):
    """
    Test that invalid campaign IDs return 404.
    """
    try:
        response = requests.get(f"{api_base_url}/api/campaigns/INVALID-999")
        assert response.status_code == 404
    except requests.exceptions.ConnectionError:
        pytest.skip("❌ API server is not running")
