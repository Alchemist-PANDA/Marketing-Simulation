import streamlit as st
import uuid
import hashlib
from src.ui.auth_ui import require_auth
from src.core.supabase_client import SupabaseManager
from src.ui.theme import apply_theme

st.set_page_config(page_title="API Keys", page_icon="🔑", layout="wide")
apply_theme()
require_auth()

st.title("API Key Management")
st.markdown("Generate API keys for programmatic access to the Simulation Engine.")

user_id = st.session_state["user"]["id"]
manager = SupabaseManager()

def generate_key(name: str):
    raw_key = f"sk_test_{uuid.uuid4().hex}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    data = {
        "user_id": user_id,
        "key_hash": key_hash,
        "name": name,
        "permissions": {"read": True, "write": True},
        "rate_limit": 10
    }
    res = manager.insert("api_keys", data)
    if res.get("status") == "success":
        st.session_state["new_key"] = raw_key
        st.success("API Key generated successfully!")
    else:
        st.error(f"Failed to generate key: {res.get('message')}")

def revoke_key(key_id: str):
    client = manager._get_client()
    if client:
        try:
            client.table("api_keys").delete().eq("id", key_id).execute()
            st.success("Key revoked.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to revoke key: {e}")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Create New Key")
    with st.form("new_key_form"):
        key_name = st.text_input("Key Name (e.g. 'Production Backend')")
        submit = st.form_submit_button("Generate Key")
        if submit:
            if not key_name:
                st.error("Please provide a name for the key.")
            else:
                generate_key(key_name)

    if "new_key" in st.session_state:
        st.warning("⚠️ Make sure to copy your API key now. You won't be able to see it again!")
        st.code(st.session_state["new_key"])
        if st.button("I have copied my key"):
            del st.session_state["new_key"]
            st.rerun()

with col2:
    st.subheader("Your Active Keys")
    res = manager.select("api_keys", filters={"user_id": user_id})
    if res.get("status") == "success" and res.get("data"):
        keys = res["data"]
        for key in keys:
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{key['name']}**")
                c2.write(f"Created: {key['created_at'][:10]}")
                if c3.button("Revoke", key=f"revoke_{key['id']}"):
                    revoke_key(key['id'])
                st.divider()
    else:
        st.info("You don't have any active API keys.")
