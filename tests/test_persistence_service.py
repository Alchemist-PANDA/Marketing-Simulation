import pytest
from src.services.persistence_service import PersistenceService
from src.core.supabase_client import SupabaseManager

def test_persistence_local_mode_rejection(monkeypatch):
    """Verify that local mode returns disabled status with saved=False and id=None."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    service = PersistenceService()

    # Test all methods
    res1 = service.save_campaign("u1", "C1", "fb", 100.0)
    res2 = service.save_ad_variant("u1", "c1", "text", 20.0, "cat", {})
    res3 = service.save_simulation_run("u1", "v1", {})

    for res in [res1, res2, res3]:
        assert res["status"] == "disabled"
        assert res["saved"] is False
        assert res["id"] is None
        assert "Persistence disabled" in res["message"]

def test_save_campaign_payload_construction(monkeypatch):
    """Verify that save_campaign constructs the correct Supabase payload."""
    # Mock manager to avoid network calls
    class MockManager:
        enabled = True
        def insert(self, table, payload):
            assert table == "campaigns"
            assert payload["user_id"] == "user-123"
            assert payload["name"] == "Test Campaign"
            assert payload["channel"] == "instagram"
            assert payload["budget"] == 500.0
            return {"status": "success", "data": [{"id": "uuid-123"}]}

    monkeypatch.setenv("SUPABASE_URL", "http://test.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "key")

    service = PersistenceService()
    service.manager = MockManager()

    res = service.save_campaign("user-123", "Test Campaign", "instagram", 500.0)
    assert res["status"] == "success"
    assert res["saved"] is True
    assert res["id"] == "uuid-123"

def test_save_ad_variant_payload_construction(monkeypatch):
    """Verify that save_ad_variant constructs the correct Supabase payload."""
    class MockManager:
        enabled = True
        def insert(self, table, payload):
            assert table == "ad_variants"
            assert payload["scores_json"] == {"score": 0.9}
            assert payload["price"] == 25.5
            return {"status": "success", "data": [{"id": "v-uuid"}]}

    monkeypatch.setenv("SUPABASE_URL", "http://test.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "key")

    service = PersistenceService()
    service.manager = MockManager()

    res = service.save_ad_variant("u1", "c1", "text", 25.5, "cat", {"score": 0.9})
    assert res["saved"] is True
    assert res["id"] == "v-uuid"

def test_save_simulation_run_payload_construction(monkeypatch):
    """Verify that save_simulation_run constructs the correct Supabase payload."""
    class MockManager:
        enabled = True
        def insert(self, table, payload):
            assert table == "simulation_runs"
            assert payload["variant_id"] == "v-1"
            assert payload["results_json"] == {"ctr": 0.05}
            return {"status": "success", "data": [{"id": "r-uuid"}]}

    monkeypatch.setenv("SUPABASE_URL", "http://test.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "key")

    service = PersistenceService()
    service.manager = MockManager()

    res = service.save_simulation_run("u1", "v-1", {"ctr": 0.05})
    assert res["saved"] is True
    assert res["id"] == "r-uuid"

def test_persistence_error_handling(monkeypatch):
    """Verify that manager errors return status=error and saved=false."""
    class MockManager:
        enabled = True
        def insert(self, table, payload):
            return {"status": "error", "message": "Database full"}

    monkeypatch.setenv("SUPABASE_URL", "http://test.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "key")

    service = PersistenceService()
    service.manager = MockManager()

    res = service.save_campaign("u1", "C1", "ch", 10.0)
    assert res["status"] == "error"
    assert res["saved"] is False
    assert res["id"] is None
    assert "Database full" in res["message"]

def test_list_campaigns_local_mode(monkeypatch):
    """Verify list_campaigns respects local mode."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    service = PersistenceService()
    res = service.list_campaigns("u1")
    assert res["status"] == "disabled"
    assert "data" not in res

def test_list_campaigns_success(monkeypatch):
    """Verify list_campaigns correctly queries and sorts."""
    class MockManager:
        enabled = True
        def select(self, table, filters):
            assert table == "campaigns"
            assert filters == {"user_id": "u1"}
            return {"status": "success", "data": [
                {"id": "1", "created_at": "2026-05-01"},
                {"id": "2", "created_at": "2026-05-03"},
                {"id": "3", "created_at": "2026-05-02"}
            ]}

    monkeypatch.setenv("SUPABASE_URL", "http://test.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "key")

    service = PersistenceService()
    service.manager = MockManager()

    res = service.list_campaigns("u1")
    assert res["status"] == "success"
    # Should be sorted desc
    assert [c["id"] for c in res["data"]] == ["2", "3", "1"]
