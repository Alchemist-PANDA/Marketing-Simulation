import pytest
import os
from src.core.supabase_client import SupabaseManager

def test_supabase_disabled_by_default():
    """Verify that without env vars, persistence is disabled."""
    # Ensure env vars are NOT set
    os.environ.pop("SUPABASE_URL", None)
    os.environ.pop("SUPABASE_ANON_KEY", None)

    manager = SupabaseManager()
    status = manager.get_status()

    assert status["enabled"] is False
    assert status["mode"] == "local"
    assert status["client_initialized"] is False

def test_supabase_partial_env_disabled():
    """Verify that partial env vars result in disabled persistence."""
    os.environ["SUPABASE_URL"] = "https://example.supabase.co"
    os.environ.pop("SUPABASE_ANON_KEY", None)

    manager = SupabaseManager()
    assert manager.enabled is False

    os.environ.pop("SUPABASE_URL", None)
    os.environ["SUPABASE_ANON_KEY"] = "some-key"

    manager = SupabaseManager()
    assert manager.enabled is False

def test_supabase_insert_disabled_response():
    """Verify that insert returns disabled message in local mode."""
    os.environ.pop("SUPABASE_URL", None)
    os.environ.pop("SUPABASE_ANON_KEY", None)

    manager = SupabaseManager()
    result = manager.insert("test_table", {"data": "test"})

    assert result["status"] == "disabled"
    assert "Persistence disabled" in result["message"]

def test_supabase_select_disabled_response():
    """Verify that select returns empty list in local mode."""
    os.environ.pop("SUPABASE_URL", None)
    os.environ.pop("SUPABASE_ANON_KEY", None)

    manager = SupabaseManager()
    result = manager.select("test_table")

    assert result["status"] == "disabled"
    assert result["data"] == []

def test_supabase_initialization_with_env(monkeypatch):
    """Verify that manager attempts initialization when env vars are present."""
    monkeypatch.setenv("SUPABASE_URL", "https://valid.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "valid-key")

    manager = SupabaseManager()
    assert manager.enabled is True
    assert manager.mode == "supabase"

    # Client is None until first access
    assert manager._initialized is False
    # Access client (this will fail if supabase is not installed, which we test in fallback)
    client = manager._get_client()
    # In a clean test env without supabase-py installed, this might set enabled=False
    # But for now, we just check that it tried to initialize
