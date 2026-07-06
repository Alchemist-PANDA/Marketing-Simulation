import streamlit as st
from src.core.supabase_client import SupabaseManager

st.set_page_config(page_title="Register", page_icon="📝", layout="centered", initial_sidebar_state="collapsed")

from src.ui.auth_ui import inject_auth_css

inject_auth_css()

st.markdown('<h1>Create Account</h1>', unsafe_allow_html=True)

with st.form("register_form"):
    email = st.text_input("Email", placeholder="you@company.com")
    password = st.text_input("Password", type="password", placeholder="Min 6 characters")
    password_confirm = st.text_input("Confirm Password", type="password")
    submit = st.form_submit_button("Sign Up")

if submit:
    if not email or not password:
        st.error("Please fill in all fields.")
    elif password != password_confirm:
        st.error("Passwords do not match.")
    elif len(password) < 6:
        st.error("Password must be at least 6 characters.")
    else:
        manager = SupabaseManager()
        client = manager._get_client()
        if client:
            try:
                with st.spinner("Creating account..."):
                    res = client.auth.sign_up({"email": email, "password": password})
                    if res.user:
                        st.success("Registration successful! Please check your email to verify your account (if enabled) and then login.")
                    else:
                        st.error("Registration failed. Please try again.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Supabase client not configured.")

st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
if st.button("Back to Login"):
    st.switch_page("pages/_Login.py")
st.markdown('</div>', unsafe_allow_html=True)
