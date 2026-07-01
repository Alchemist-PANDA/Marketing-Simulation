import streamlit as st
from src.core.supabase_client import SupabaseManager

st.set_page_config(page_title="Register", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at center, #1e1e2f 0%, #0a0a12 100%);
    }
    .main .block-container {
        max-width: 450px !important;
        padding: 2.5rem !important;
        margin-top: 15vh !important;
        background: rgba(20, 20, 30, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5) !important;
        color: white !important;
    }
    h1 {
        text-align: center;
        background: linear-gradient(90deg, #bb86fc, #03dac6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #6200ea 0%, #03dac6 100%);
        border: none;
        color: white;
        width: 100%;
        font-weight: bold;
    }
    .secondary-btn>button {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: none !important;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Create Account")

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
    st.switch_page("pages/0_🔐_Login.py")
st.markdown('</div>', unsafe_allow_html=True)
