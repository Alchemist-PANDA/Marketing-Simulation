"""
Authentication utilities for the Marketing Simulation project.
Provides shared logic for checking auth status and returning fallback users.
"""
import os
from dotenv import load_dotenv
load_dotenv()
from typing import Dict, Any, Optional

def is_auth_enabled() -> bool:
    """
    Check if Supabase authentication is enabled based on environment variables.
    Returns True only if both SUPABASE_URL and SUPABASE_ANON_KEY are present
    and we are NOT explicitly in a 'development' environment without keys.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    env = os.getenv("ENV", "production").lower()
    
    # If running pytest, bypass Streamlit secrets and production checks
    if "PYTEST_CURRENT_TEST" in os.environ:
        return bool(url and key)
        
    try:
        import streamlit as st
        if "SUPABASE_URL" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
        if "SUPABASE_ANON_KEY" in st.secrets:
            key = st.secrets["SUPABASE_ANON_KEY"]
        if "ENV" in st.secrets:
            env = st.secrets["ENV"].lower()
    except Exception:
        pass
    
    # In production, ALWAYS enforce auth. If keys are missing, show a clear error.
    if env != "development":
        if not (url and key):
            import streamlit as st
            st.error("Authentication Error: Supabase credentials not found in production. Please check Streamlit Cloud Secrets.")
            st.stop()
        return True
        
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

import streamlit as st

def set_user_session(user: Dict[str, Any]):
    st.session_state.user = user

def get_user_session() -> Optional[Dict[str, Any]]:
    return st.session_state.get("user")


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get an attribute or key from user session dict/Pydantic object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    
    # Try direct attribute lookup
    if hasattr(obj, key):
        return getattr(obj, key)
        
    # Helper mapping for expected fields
    if key == "is_authenticated":
        return True
    if key == "mode":
        return "supabase"
        
    # Metadata fallback for roles/plans
    if key in ("role", "plan"):
        app_metadata = getattr(obj, "app_metadata", {}) or {}
        user_metadata = getattr(obj, "user_metadata", {}) or {}
        val = app_metadata.get(key) or user_metadata.get(key) or app_metadata.get("role") or user_metadata.get("role")
        if val:
            return val
            
    return default


