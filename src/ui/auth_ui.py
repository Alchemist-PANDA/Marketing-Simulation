"""
Streamlit authentication UI components.
Provides logout form and auth status display for the sidebar, plus RBAC helpers.
"""
import streamlit as st
from typing import List, Optional
from src.core.auth_utils import is_auth_enabled, get_local_user
from src.core.supabase_client import SupabaseManager
from src.ui.theme import inject_galaxy_background



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
        st.switch_page("pages/_Login.py")


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
            st.switch_page("pages/_Login.py")


def handle_logout():
    """Handle logout and clear session state."""
    token = st.session_state.get("access_token")

    if token:
        manager = SupabaseManager()
        manager.sign_out(token)

    st.session_state["user"] = None
    st.session_state["access_token"] = None
    st.switch_page("pages/_Login.py")


def inject_auth_css():
    """Injects 3D glassmorphism UI matching the landing page."""
    inject_galaxy_background()
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* Hide Sidebar completely for public pages */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] { 
        display: none !important; 
    }
    #MainMenu, footer { display: none !important; }

    /* 3D Animated Background Reset to reveal galaxy canvas */
    .stApp, .main, [data-testid="stAppViewContainer"], header[data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stApp::before {
        content: ''; position: fixed; top: -20%; left: -10%; width: 60%; height: 60%;
        background: radial-gradient(circle, rgba(167, 139, 250, 0.15) 0%, transparent 70%);
        filter: blur(60px); animation: float1 15s ease-in-out infinite; z-index: 0; pointer-events: none;
    }
    .stApp::after {
        content: ''; position: fixed; bottom: -20%; right: -10%; width: 60%; height: 60%;
        background: radial-gradient(circle, rgba(96, 165, 250, 0.1) 0%, transparent 70%);
        filter: blur(60px); animation: float2 18s ease-in-out infinite; z-index: 0; pointer-events: none;
    }
    @keyframes float1 { 0%, 100% { transform: translate(0, 0) scale(1); } 50% { transform: translate(5%, 5%) scale(1.1); } }
    @keyframes float2 { 0%, 100% { transform: translate(0, 0) scale(1); } 50% { transform: translate(-5%, -5%) scale(1.1); } }

    /* Glass Card Container */
    .main .block-container,
    [data-testid="stAppViewBlockContainer"],
    [data-testid="block-container"] {
        position: relative; z-index: 10;
        max-width: 440px !important; padding: 3rem !important; margin-top: 10vh !important;
        background: rgba(20, 23, 28, 0.6) !important;
        backdrop-filter: blur(24px) !important; -webkit-backdrop-filter: blur(24px) !important;
        border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.05) !important;
        color: white !important; animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }

    /* Typography */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; font-size: 32px !important;
        background: linear-gradient(135deg, #a78bfa, #60a5fa) !important;
        -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
        text-align: center !important; margin-bottom: 2rem !important; letter-spacing: -0.02em !important;
    }
    
    .stMarkdown p { text-align: center !important; color: rgba(255,255,255,0.7) !important; }

    /* Input Fields */
    .stTextInput > div > div > input {
        background: #0B0D10 !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 10px !important;
        color: white !important; padding: 14px 16px !important; font-family: 'Inter', sans-serif !important; font-size: 15px !important;
        transition: all 0.3s ease !important; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #a78bfa !important; box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.2), inset 0 2px 4px rgba(0,0,0,0.2) !important;
    }

    /* Buttons */
    .stButton > button {
        width: 100% !important; background: linear-gradient(135deg, #a78bfa, #60a5fa) !important;
        border: none !important; border-radius: 10px !important; padding: 12px 24px !important;
        font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 16px !important; color: white !important;
        transition: all 0.3s ease !important; box-shadow: 0 4px 15px rgba(167, 139, 250, 0.2) !important; margin-top: 1rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(167, 139, 250, 0.4) !important;
    }

    /* Links container styling */
    a { color: #a78bfa !important; text-decoration: none !important; font-size: 14px !important; transition: color 0.2s ease !important; }
    a:hover { color: #c4b5fd !important; }
    .links-container { display: flex; justify-content: space-between; margin-top: 24px; }
    </style>
    """, unsafe_allow_html=True)


