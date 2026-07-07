import streamlit as st
from src.core.supabase_client import SupabaseManager

st.set_page_config(page_title="Reset Password", page_icon="🔑", layout="centered", initial_sidebar_state="collapsed")

from src.ui.auth_ui import inject_auth_css

inject_auth_css()

st.markdown('<h1>Reset Password</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #ccc;'>Enter your email to receive a password reset link.</p>", unsafe_allow_html=True)

with st.form("reset_form"):
    email = st.text_input("Email", placeholder="you@company.com")
    submit = st.form_submit_button("Send Reset Link")

if submit:
    if not email:
        st.error("Please enter your email.")
    else:
        manager = SupabaseManager()
        with st.spinner("Sending link..."):
            result = manager.reset_password(email)
            if result.get("status") == "success":
                st.success("If an account with that email exists, a reset link has been sent.")
            else:
                st.error(f"Error: {result.get('message')}")

st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
if st.button("Back to Login"):
    st.switch_page("pages/_Login.py")
st.markdown('</div>', unsafe_allow_html=True)
