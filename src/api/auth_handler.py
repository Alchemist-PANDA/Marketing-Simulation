"""
JWT verification and user retrieval logic for FastAPI.
Handles both Supabase-authenticated and local fallback users.
"""
from typing import Optional, Dict, Any
from src.core.auth_utils import is_auth_enabled, get_local_user
from src.core.supabase_client import SupabaseManager

def get_current_user_logic(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve the current user from a JWT token or return the local fallback user.

    Args:
        token: JWT token from Authorization header (optional)

    Returns:
        User dictionary with id, email, is_authenticated, and mode fields

    Behavior:
        - If auth is disabled (no Supabase credentials), returns local user
        - If auth is enabled but no token provided, returns local user
        - If auth is enabled and token provided, verifies with Supabase
        - If token is invalid/expired, returns local user (graceful degradation)
    """
    if not is_auth_enabled():
        return get_local_user()

    if not token:
        return get_local_user()

    # Attempt to verify token with Supabase
    manager = SupabaseManager()
    try:
        user_response = manager.get_user(token)

        if user_response.get("status") == "success":
            user_data = user_response.get("user", {})
            return {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "is_authenticated": True,
                "mode": "supabase"
            }
        else:
            # Token verification failed, fall back to local user
            return get_local_user()

    except Exception:
        # Any error during verification falls back to local user
        return get_local_user()
