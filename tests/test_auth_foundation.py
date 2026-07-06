import pytest
import os
from src.core.auth_utils import is_auth_enabled, get_local_user, get_auth_mode
from src.api.auth_handler import get_current_user_logic
from src.core.supabase_client import SupabaseManager

def test_is_auth_enabled_with_both_vars(monkeypatch):
    """Verify that auth is enabled when both env vars are present."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")
    assert is_auth_enabled() is True

def test_is_auth_enabled_missing_url(monkeypatch):
    """Verify that auth is disabled when URL is missing."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")
    assert is_auth_enabled() is False

def test_is_auth_enabled_missing_key(monkeypatch):
    """Verify that auth is disabled when key is missing."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    assert is_auth_enabled() is False

def test_is_auth_enabled_both_missing(monkeypatch):
    """Verify that auth is disabled when both env vars are missing."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    assert is_auth_enabled() is False

def test_local_user_payload():
    """Verify the structure of the local fallback user."""
    user = get_local_user()
    assert user["id"] == "00000000-0000-0000-0000-000000000000"
    assert user["email"] == "dev@local.host"
    assert user["is_authenticated"] is True
    assert user["mode"] == "local"

def test_get_auth_mode_supabase(monkeypatch):
    """Verify auth mode returns 'supabase' when credentials are present."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")
    assert get_auth_mode() == "supabase"

def test_get_auth_mode_local(monkeypatch):
    """Verify auth mode returns 'local' when credentials are missing."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    assert get_auth_mode() == "local"

def test_get_current_user_logic_no_auth(monkeypatch):
    """Verify that get_current_user_logic returns local user when auth is disabled."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    user = get_current_user_logic(token="fake-token")
    assert user["id"] == "00000000-0000-0000-0000-000000000000"
    assert user["email"] == "dev@local.host"
    assert user["mode"] == "local"

def test_get_current_user_logic_no_token(monkeypatch):
    """Verify that get_current_user_logic returns local user when no token is provided."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")

    user = get_current_user_logic(token=None)
    assert user["mode"] == "local"

def test_supabase_manager_auth_methods_disabled(monkeypatch):
    """Verify that auth methods return disabled status in local mode."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    manager = SupabaseManager()

    sign_in_result = manager.sign_in("test@example.com", "password")
    assert sign_in_result["status"] == "disabled"

    sign_up_result = manager.sign_up("test@example.com", "password")
    assert sign_up_result["status"] == "disabled"

    get_user_result = manager.get_user("fake-jwt")
    assert get_user_result["status"] == "disabled"

    sign_out_result = manager.sign_out("fake-jwt")
    assert sign_out_result["status"] == "disabled"

def test_mock_user_consistency():
    """Verify that the local user has the same fields as the User model."""
    from src.api.models import User

    local_user = get_local_user()

    # Ensure all required User fields are present
    user_model = User(**local_user)
    assert user_model.id == local_user["id"]
    assert user_model.email == local_user["email"]
    assert user_model.is_authenticated == local_user["is_authenticated"]
    assert user_model.mode == local_user["mode"]
