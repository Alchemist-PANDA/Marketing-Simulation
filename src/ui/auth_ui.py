"""
Streamlit authentication UI components.
Provides logout form and auth status display for the sidebar, plus RBAC helpers.
"""
import streamlit as st
from typing import List, Optional
from src.core.auth_utils import is_auth_enabled, get_local_user
from src.core.supabase_client import SupabaseManager


def initialize_auth_session():
    """Initialize authentication session state on first run."""
    if "auth_initialized" not in st.session_state:
        st.session_state["auth_initialized"] = True
        st.session_state["auth_mode"] = "supabase" if is_auth_enabled() else "local"
        st.session_state["user"] = None
        st.session_state["access_token"] = None

        if st.session_state["auth_mode"] == "local":
            st.session_state["user"] = get_local_user()


def require_auth():
    """Enforces that a user is logged in. Redirects to Login if not."""
    initialize_auth_session()
    if not st.session_state.get("user") or not st.session_state["user"].get("is_authenticated"):
        st.warning("Please log in to access this page.")
        st.switch_page("pages/0_🔐_Login.py")


def require_role(allowed_roles: List[str]):
    """Enforces that the logged-in user has a specific role."""
    require_auth()
    user = st.session_state.get("user")
    
    # Local dev mode bypasses RBAC
    if user.get("mode") == "local":
        return
        
    user_role = user.get("role", "free")
    if user_role not in allowed_roles and "admin" not in allowed_roles:
        st.error(f"Access Denied. This feature requires one of the following roles: {', '.join(allowed_roles)}")
        st.stop()


def render_auth_sidebar():
    """Render authentication UI in the sidebar."""
    initialize_auth_session()

    auth_mode = st.session_state["auth_mode"]
    user = st.session_state["user"]

    st.sidebar.markdown("### Authentication")

    if auth_mode == "local":
        st.sidebar.success("🟢 Local Developer Mode")
        st.sidebar.caption("Running without Supabase credentials")
        return

    if user and user.get("is_authenticated") and user.get("mode") == "supabase":
        st.sidebar.success(f"🟢 Logged in as: {user.get('email')}")
        st.sidebar.caption(f"Role: **{user.get('role', 'free').upper()}**")
        if st.sidebar.button("Logout", key="logout_btn"):
            handle_logout()
    else:
        st.sidebar.warning("🔴 Not Authenticated")
        if st.sidebar.button("Go to Login"):
            st.switch_page("pages/0_🔐_Login.py")


def handle_logout():
    """Handle logout and clear session state."""
    token = st.session_state.get("access_token")

    if token:
        manager = SupabaseManager()
        manager.sign_out(token)

    st.session_state["user"] = None
    st.session_state["access_token"] = None
    st.switch_page("pages/0_🔐_Login.py")

