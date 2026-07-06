"""
Authentication utilities for the Marketing Simulation project.
Provides shared logic for checking auth status and returning fallback users.
"""
import os
from dotenv import load_dotenv
load_dotenv()
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
<<<<<<< HEAD

import streamlit as st

def set_user_session(user: Dict[str, Any]):
    st.session_state.user = user

def get_user_session() -> Optional[Dict[str, Any]]:
    return st.session_state.get("user")

=======
>>>>>>> origin/claude/marketing-sim-enterprise-7peo6y
