import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Digital Wind Tunnel – Login",
    page_icon="🌀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

from src.ui.auth_ui import inject_auth_css

# Inject global auth 3D CSS
inject_auth_css()

st.markdown('<h1>🌀 Digital Wind Tunnel</h1>', unsafe_allow_html=True)
st.markdown('<p>Predict ad performance before spending a dollar.</p>', unsafe_allow_html=True)

# Import Supabase auth functions (adjust according to your actual import)
try:
    from src.core.supabase_client import sign_in
    from src.core.auth_utils import set_user_session
except ImportError:
    st.error("Authentication modules not found. Please check your imports.")
    st.stop()

with st.form("login_form", clear_on_submit=False):
    email = st.text_input("Email", placeholder="you@company.com")
    password = st.text_input("Password", type="password", placeholder="••••••••")
    submitted = st.form_submit_button("Sign In")

if submitted:
    if not email or not password:
        st.error("Please fill in all fields.")
    else:
        with st.spinner("Signing in..."):
            result = sign_in(email, password)
            if result.get("status") == "success":
                set_user_session(result["user"])
                st.success("✅ Login successful! Redirecting...")
                st.switch_page("app.py")  # Redirect to dashboard
            else:
                st.error(f"❌ {result.get('message', 'Login failed.')}")

st.markdown("""
<div class="links-container">
    <a href="/_Register" target="_self">Create Account</a>
    <a href="/_ResetPassword" target="_self">Forgot Password?</a>
</div>
""", unsafe_allow_html=True)
