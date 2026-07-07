"""
Streamlit authentication UI components.
Provides login/logout forms and auth status display for the sidebar.
"""
import streamlit as st
from typing import Dict, Any, Optional
from src.core.auth_utils import is_auth_enabled, get_local_user
from src.core.supabase_client import SupabaseManager


def initialize_auth_session():
    """Initialize authentication session state on first run."""
    if "auth_initialized" not in st.session_state:
        st.session_state["auth_initialized"] = True
        st.session_state["auth_mode"] = "supabase" if is_auth_enabled() else "local"
        st.session_state["user"] = None
        st.session_state["access_token"] = None

        # In local mode, auto-authenticate with local user
        if st.session_state["auth_mode"] == "local":
            st.session_state["user"] = get_local_user()


def render_auth_sidebar():
    """Render authentication UI in the sidebar."""
    initialize_auth_session()

    auth_mode = st.session_state["auth_mode"]
    user = st.session_state["user"]

    st.sidebar.markdown("### Authentication")

    # Local Mode: Show status only
    if auth_mode == "local":
        st.sidebar.success("🟢 Local Developer Mode")
        st.sidebar.caption("Running without Supabase credentials")
        return

    # Supabase Mode: Show login/logout UI
    if user and user.get("is_authenticated") and user.get("mode") == "supabase":
        # User is logged in
        st.sidebar.success(f"🟢 Logged in as: {user.get('email')}")
        if st.sidebar.button("Logout", key="logout_btn"):
            handle_logout()
    else:
        # User is not logged in
        st.sidebar.warning("🔴 Not Authenticated")
        render_login_form()


def render_login_form():
    """Render the login form in Supabase mode."""
    with st.sidebar.form("login_form"):
        st.markdown("#### Sign In")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Sign In")

        if submit:
            if not email or not password:
                st.error("❌ Email and password are required")
            else:
                handle_login(email, password)


def handle_login(email: str, password: str):
    """Handle login attempt with Supabase."""
    manager = SupabaseManager()

    try:
        response = manager.sign_in(email, password)

        if response.get("status") == "success":
            # Extract session and user
            session = response.get("session")
            user_data = response.get("user")

            if session and user_data:
                st.session_state["access_token"] = session.access_token
                st.session_state["user"] = {
                    "id": user_data.id,
                    "email": user_data.email,
                    "is_authenticated": True,
                    "mode": "supabase"
                }
                st.rerun()
            else:
                st.error("❌ Login failed: Invalid response from auth service")

        elif response.get("status") == "disabled":
            # Supabase credentials present but client failed to initialize
            st.error("⚠️ Auth service unavailable. Please contact support.")

        else:
            # Login failed (invalid credentials or other error)
            error_msg = response.get("message", "Unknown error")
            st.error(f"❌ Login failed: {error_msg}")

    except Exception as e:
        st.error(f"⚠️ Connection error: {str(e)}")


def handle_logout():
    """Handle logout and clear session state."""
    token = st.session_state.get("access_token")

    if token:
        manager = SupabaseManager()
        manager.sign_out(token)

    # Clear session state
    st.session_state["user"] = None
    st.session_state["access_token"] = None
    st.rerun()
