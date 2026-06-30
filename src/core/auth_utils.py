"""
Authentication utilities for the Marketing Simulation project.
Provides shared logic for checking auth status and returning fallback users.
"""
import os
from typing import Dict, Any, Optional

def is_auth_enabled() -> bool:
    """
    Check if Supabase authentication is enabled based on environment variables.
    Returns True only if both SUPABASE_URL and SUPABASE_ANON_KEY are present.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    return bool(url and key)

def get_local_user() -> Dict[str, Any]:
    """
    Returns a static local developer user for fallback mode.
    This user is used when Supabase credentials are not available.
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": "dev@local.host",
        "is_authenticated": True,
        "mode": "local"
    }

def get_auth_mode() -> str:
    """Returns the current authentication mode: 'supabase' or 'local'."""
    return "supabase" if is_auth_enabled() else "local"
