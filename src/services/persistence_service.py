"""
Persistence service for saving campaigns, ad variants, and simulation runs.
Enforces strict local-mode behavior (no silent saves, no mock IDs).
"""
from typing import Dict, Any, Optional, List
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

    # ── Report History (simulation_reports table) ──

    def save_report(self, user_id: str, result: Dict[str, Any],
                    ad1_text: str, ad2_text: str, channel: str,
                    num_agents: int, objective: str = "",
                    campaign_name: str = "") -> Dict[str, Any]:
        """Save a simulation report and auto-assign a report number."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        report_number = self._next_report_number(user_id)

        payload = {
            "user_id": user_id,
            "report_number": report_number,
            "ad_a_text": ad1_text,
            "ad_b_text": ad2_text,
            "winner": result.get("winner", ""),
            "lift_percentage": result.get("lift_percentage", 0),
            "objective": objective or result.get("objective", ""),
            "channel": channel,
            "num_agents": num_agents,
            "campaign_name": campaign_name,
            "result_json": result,
        }

        res = self.manager.insert("simulation_reports", payload)
        if res.get("status") == "success":
            data = res.get("data", [{}])[0]
            return {"status": "success", "saved": True, "id": data.get("id"),
                    "report_number": report_number, "data": data}
        return {"status": "error", "saved": False, "id": None,
                "message": res.get("message", "Unknown error saving report")}

    def _next_report_number(self, user_id: str) -> int:
        """Compute the next report number for a user."""
        res = self.manager.select("simulation_reports", filters={"user_id": user_id})
        if res.get("status") == "success":
            return len(res.get("data", [])) + 1
        return 1

    def list_reports(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """List simulation reports for a user, newest first."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        res = self.manager.select("simulation_reports", filters={"user_id": user_id})
        if res.get("status") == "success":
            data = res.get("data", [])
            data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return {"status": "success", "data": data[:limit]}
        return {"status": "error", "data": [],
                "message": res.get("message", "Unknown error listing reports")}

    def get_report(self, report_id: str, user_id: str) -> Dict[str, Any]:
        """Fetch a single report by ID, verifying ownership."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        res = self.manager.select("simulation_reports",
                                  filters={"id": report_id, "user_id": user_id})
        if res.get("status") == "success" and res.get("data"):
            return {"status": "success", "data": res["data"][0]}
        return {"status": "error", "message": "Report not found or access denied"}

    def delete_report(self, report_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a report by ID, verifying ownership."""
        if not is_auth_enabled() or not self.manager.enabled:
            return self._disabled_response()

        client = self.manager._get_client()
        if not client:
            return {"status": "error", "message": "Database unavailable"}
        try:
            response = (client.table("simulation_reports")
                        .delete()
                        .eq("id", report_id)
                        .eq("user_id", user_id)
                        .execute())
            return {"status": "success", "data": response.data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
