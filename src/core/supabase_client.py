import os
from typing import Dict, Any, Optional

class SupabaseManager:
    """
    Wrapper for Supabase client with lazy initialization and robust local fallback.
    """
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self._client = None
        self._initialized = False

        # Determine mode based on env vars
        self.mode = "supabase" if (self.url and self.key) else "local"
        self.enabled = self.mode == "supabase"

    def _get_client(self):
        """Lazily initialize the Supabase client only when needed."""
        if not self.enabled:
            return None

        if self._initialized:
            return self._client

        try:
            from supabase import create_client, Client
            self._client = create_client(self.url, self.key)
            self._initialized = True
            return self._client
        except ImportError:
            # If supabase-py is not installed, fail gracefully to local mode
            self.enabled = False
            self.mode = "local"
            return None
        except Exception as e:
            # Catch bad URLs or keys
            self.enabled = False
            self.mode = "local"
            return None

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

# Singleton instance
supabase_manager = SupabaseManager()
