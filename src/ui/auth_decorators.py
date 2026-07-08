import streamlit as st
from functools import wraps
from src.core.auth_utils import safe_get

def require_role(allowed_roles: list[str]):
    """
    Streamlit decorator to enforce role-based access control.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user" not in st.session_state or st.session_state.user is None:
                st.warning("Please log in to access this page.")
                st.stop()
                
            user = st.session_state.user
            if safe_get(user, "mode") == "local":
                return func(*args, **kwargs)
                
            user_plan = safe_get(user, "plan", "free")
            if user_plan not in allowed_roles and "admin" not in allowed_roles:
                st.error(f"Access Denied. This feature requires one of the following plans: {', '.join(allowed_roles)}")
                st.info("Please upgrade your plan to access premium features.")
                st.stop()
                
            return func(*args, **kwargs)
        return wrapper
    return decorator
