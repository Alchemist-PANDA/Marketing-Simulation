import os
from dotenv import load_dotenv
load_dotenv()
from typing import Dict, Any, Optional

class SupabaseManager:
    """
    Wrapper for Supabase client with lazy initialization and robust local fallback.
    """
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.env = os.getenv("ENV", "production").lower()
        
        try:
            import streamlit as st
            if "SUPABASE_URL" in st.secrets:
                self.url = st.secrets["SUPABASE_URL"]
            if "SUPABASE_ANON_KEY" in st.secrets:
                self.key = st.secrets["SUPABASE_ANON_KEY"]
            if "SUPABASE_SERVICE_ROLE_KEY" in st.secrets:
                self.service_role_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
            if "ENV" in st.secrets:
                self.env = st.secrets["ENV"].lower()
        except Exception:
            pass
            
        self._client = None
        self._initialized = False

        # Determine mode based on env vars
        if self.env == "development" and not (self.url and self.key):
            self.mode = "local"
            self.enabled = False
        else:
            self.mode = "supabase"
            self.enabled = True

    def _get_client(self):
        """Lazily initialize the Supabase client only when needed."""
        if not self.enabled:
            return None

        if self._initialized:
            return self._client

        if not self.url or not self.key:
            if self.env == "development":
                self.enabled = False
                self.mode = "local"
                return None
            else:
                import streamlit as st
                st.error("Authentication Error: Supabase credentials (SUPABASE_URL, SUPABASE_ANON_KEY) are missing in production. Please check Streamlit Cloud Secrets.")
                st.stop()

        try:
            from supabase import create_client, Client
            self._client = create_client(self.url, self.key)
            self._initialized = True
            return self._client
        except ImportError as e:
            # If supabase-py is not installed, fail gracefully to local mode
            if self.env == "development":
                self.enabled = False
                self.mode = "local"
                return None
            else:
                import streamlit as st
                st.error(f"Authentication Error: supabase-py is not installed but required in production. {e}")
                st.stop()
        except Exception as e:
            # Catch bad URLs or keys
            if self.env == "development":
                self.enabled = False
                self.mode = "local"
                return None
            else:
                import streamlit as st
                import traceback
                error_trace = traceback.format_exc()
                st.error(f"Failed to initialize Supabase client. Exception: {e}")
                st.code(error_trace, language="python")
                st.stop()

    def get_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the persistence layer."""
        # Check if we can instantiate it
        self._get_client()
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "client_initialized": self._initialized
        }

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into a Supabase table, or return disabled status."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": f"Persistence disabled. Data not saved to {table}."}

        try:
            # We don't execute yet as we need .execute() which makes it a real call
            # but for safety/interface definition, we'll try to execute it
            response = client.table(table).insert(data).execute()
            return {"status": "success", "data": response.data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def update(self, table: str, filters: dict, data: dict) -> dict:
        """Update data in a Supabase table."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": f"Persistence disabled."}
        try:
            q = client.table(table).update(data)
            for k, v in filters.items():
                q = q.eq(k, v)
            response = q.execute()
            return {"status": "success", "data": response.data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def select(self, table: str, query: str = "*", filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Select data from a Supabase table, or return disabled status."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "data": [], "message": "Persistence disabled."}

        try:
            q = client.table(table).select(query)
            if filters:
                for k, v in filters.items():
                    q = q.eq(k, v)
            response = q.execute()
            return {"status": "success", "data": response.data}
        except Exception as e:
            return {"status": "error", "data": [], "message": str(e)}

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in with email and password."""
        
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": "Auth disabled. Use local mode."}

        try:
            response = client.auth.sign_in_with_password({"email": email, "password": password})
            return {
                "status": "success",
                "session": response.session,
                "user": response.user
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user with email and password."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": "Auth disabled. Use local mode."}

        try:
            response = client.auth.sign_up({"email": email, "password": password})
            return {
                "status": "success",
                "session": response.session,
                "user": response.user
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_user(self, jwt: str) -> Dict[str, Any]:
        """Verify JWT and retrieve user information."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": "Auth disabled. Use local mode."}

        try:
            response = client.auth.get_user(jwt)
            return {
                "status": "success",
                "user": response.user
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def sign_out(self, jwt: str) -> Dict[str, Any]:
        """Sign out the current user."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": "Auth disabled. Use local mode."}

        try:
            client.auth.sign_out()
            return {"status": "success", "message": "Signed out successfully."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def reset_password(self, email: str) -> Dict[str, Any]:
        """Send a password reset email."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": "Auth disabled. Use local mode."}

        try:
            response = client.auth.reset_password_email(email)
            return {"status": "success", "message": "Reset email sent successfully."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def update_password(self, new_password: str) -> Dict[str, Any]:
        """Update password for logged in user."""
        client = self._get_client()
        if not client or not self.enabled:
            return {"status": "disabled", "message": "Auth disabled. Use local mode."}
            
        try:
            response = client.auth.update_user({"password": new_password})
            return {"status": "success", "user": response.user}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Singleton instance
supabase_manager = SupabaseManager()

def sign_in(email: str, password: str) -> Dict[str, Any]:
    return supabase_manager.sign_in(email, password)

def sign_up(email: str, password: str) -> Dict[str, Any]:
    return supabase_manager.sign_up(email, password)

def get_current_user(jwt: str = None) -> Dict[str, Any]:
    if jwt:
        return supabase_manager.get_user(jwt)
    return {"status": "error", "message": "No JWT provided"}

def sign_out(jwt: str = None) -> Dict[str, Any]:
    return supabase_manager.sign_out(jwt)

