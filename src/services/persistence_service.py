"""
Persistence service for saving campaigns, ad variants, and simulation runs.
Enforces strict local-mode behavior (no silent saves, no mock IDs).
"""
from typing import Dict, Any, Optional
from src.core.supabase_client import SupabaseManager
from src.core.auth_utils import is_auth_enabled

class PersistenceService:
    """Service layer for database persistence."""

    def __init__(self):
        self.manager = SupabaseManager()

    def _disabled_response(self) -> Dict[str, Any]:
        """Standard response when persistence is disabled."""
        return {
            "status": "disabled",
            "saved": False,
            "id": None,
            "message": "Persistence disabled in local mode"
        }

    def save_campaign(self, user_id: str, name: str, channel: str, budget: float) -> Dict[str, Any]:
        """Save a campaign record."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        payload = {
            "user_id": user_id,
            "name": name,
            "channel": channel,
            "budget": budget
        }

        result = self.manager.insert("campaigns", payload)

        if result.get("status") == "success":
            # Supabase returns a list of inserted records; take the first one
            data = result.get("data", [{}])[0]
            return {
                "status": "success",
                "saved": True,
                "id": data.get("id"),
                "data": data
            }

        return {
            "status": "error",
            "saved": False,
            "id": None,
            "message": result.get("message", "Unknown error saving campaign")
        }

    def save_ad_variant(self, user_id: str, campaign_id: Optional[str], text: str,
                        price: float, category: str, scores: Dict[str, Any]) -> Dict[str, Any]:
        """Save an ad variant record."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        payload = {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "text": text,
            "price": price,
            "category": category,
            "scores_json": scores
        }

        result = self.manager.insert("ad_variants", payload)

        if result.get("status") == "success":
            data = result.get("data", [{}])[0]
            return {
                "status": "success",
                "saved": True,
                "id": data.get("id"),
                "data": data
            }

        return {
            "status": "error",
            "saved": False,
            "id": None,
            "message": result.get("message", "Unknown error saving ad variant")
        }

    def save_simulation_run(self, user_id: str, variant_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Save a simulation run record."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        payload = {
            "user_id": user_id,
            "variant_id": variant_id,
            "results_json": results
        }

        result = self.manager.insert("simulation_runs", payload)

        if result.get("status") == "success":
            data = result.get("data", [{}])[0]
            return {
                "status": "success",
                "saved": True,
                "id": data.get("id"),
                "data": data
            }

        return {
            "status": "error",
            "saved": False,
            "id": None,
            "message": result.get("message", "Unknown error saving simulation run")
        }

    def list_campaigns(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """List campaigns for a user, ordered by created_at desc."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        result = self.manager.select("campaigns", filters={"user_id": user_id})

        if result.get("status") == "success":
            data = result.get("data", [])
            # Sort by created_at desc (manager select doesn't support order yet)
            data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return {
                "status": "success",
                "data": data[:limit]
            }

        return {
            "status": "error",
            "message": result.get("message", "Unknown error listing campaigns"),
            "data": []
        }

    def get_campaign_details(self, campaign_id: str, user_id: str) -> Dict[str, Any]:
        """Fetch variants and runs for a specific campaign."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        # 1. Verify campaign belongs to user and get it
        camp_res = self.manager.select("campaigns", filters={"id": campaign_id, "user_id": user_id})
        if camp_res.get("status") != "success" or not camp_res.get("data"):
            return {"status": "error", "message": "Campaign not found or access denied"}

        campaign = camp_res["data"][0]

        # 2. Get variants
        var_res = self.manager.select("ad_variants", filters={"campaign_id": campaign_id, "user_id": user_id})
        if var_res.get("status") != "success":
            return {"status": "error", "message": "Failed to load variants"}

        variants = var_res.get("data", [])

        # 3. Get runs for each variant
        full_variants = []
        for variant in variants:
            run_res = self.manager.select("simulation_runs", filters={"variant_id": variant["id"], "user_id": user_id})
            runs = run_res.get("data", []) if run_res.get("status") == "success" else []
            variant["runs"] = runs
            full_variants.append(variant)

        return {
            "status": "success",
            "campaign": campaign,
            "variants": full_variants
        }
