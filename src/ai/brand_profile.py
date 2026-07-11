"""
Persistent brand profile — the root of the expert copilot (plan Section 3.1).

Every recommendation the copilot makes should be grounded in this profile:
business model (B2C/B2B/hybrid), business stage, a *live* budget, brand voice,
ICP, competitors, active channels and seasonality. The profile is:

  • kept in st.session_state so it's available to the copilot every turn, and
  • persisted to Supabase (table ``brand_profiles``) for logged-in users so it
    survives across sessions.

Corrections are first-class (plan Section 3.6): every save stamps ``updated_at``
and appends a timestamped entry to ``change_log`` so advice regressions can be
traced back to a bad assumption.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st

_SS_PROFILE = "brand_profile"

# Field keys and human labels used by the intake form and the context builder.
FIELDS = [
    ("business_name", "Business / product name"),
    ("business_model", "Business model (B2C / B2B / Hybrid)"),
    ("business_stage", "Business stage (pre-revenue / early growth / scaling / mature)"),
    ("monthly_budget", "Monthly marketing budget"),
    ("brand_voice", "Brand voice (3–5 adjectives)"),
    ("icp", "Ideal customer profile (ICP)"),
    ("competitors", "Key competitors to differentiate from"),
    ("active_channels", "Active marketing channels"),
    ("seasonality", "Seasonality / known high-low periods"),
]

EMPTY_PROFILE: Dict[str, Any] = {k: "" for k, _ in FIELDS}


def get_profile() -> Dict[str, Any]:
    """Return the current profile (session first, then Supabase for logged-in users)."""
    if _SS_PROFILE in st.session_state:
        return st.session_state[_SS_PROFILE]

    profile = dict(EMPTY_PROFILE)
    loaded = _load_from_supabase()
    if loaded:
        profile.update({k: loaded.get(k, "") for k in EMPTY_PROFILE})
        profile["change_log"] = loaded.get("change_log", [])
        profile["updated_at"] = loaded.get("updated_at", "")
    st.session_state[_SS_PROFILE] = profile
    return profile


def is_configured() -> bool:
    """True once the load-bearing fields (model + stage) are filled in."""
    p = get_profile()
    return bool(p.get("business_model")) and bool(p.get("business_stage"))


def save_profile(new_values: Dict[str, Any]) -> Dict[str, Any]:
    """Merge and persist profile changes, logging what changed with a timestamp."""
    current = get_profile()
    now = datetime.now(timezone.utc).isoformat()

    changes: List[str] = []
    for k, _label in FIELDS:
        if k in new_values and str(new_values[k]).strip() != str(current.get(k, "")).strip():
            changes.append(f"{k}: '{current.get(k, '')}' → '{new_values[k]}'")
            current[k] = new_values[k]

    if changes:
        log = current.get("change_log", [])
        log.append({"at": now, "changes": changes})
        current["change_log"] = log[-50:]  # keep the most recent 50 edits
        current["updated_at"] = now
        st.session_state[_SS_PROFILE] = current
        _save_to_supabase(current)

    return current


def profile_context(profile: Optional[Dict[str, Any]] = None) -> str:
    """Render the profile as a context block for the copilot system prompt."""
    p = profile or get_profile()
    filled = [(label, p.get(k)) for k, label in FIELDS if str(p.get(k, "")).strip()]
    if not filled:
        return ""
    lines = ["\n\n--- BRAND PROFILE (ground every recommendation in this) ---"]
    lines += [f"{label}: {val}" for label, val in filled]
    if p.get("updated_at"):
        lines.append(f"(profile last updated {p['updated_at'][:10]})")
    lines.append("--- END BRAND PROFILE ---")
    return "\n".join(lines)


# ── Supabase persistence (best-effort; no-ops in local mode) ──────────────────

def _user_id() -> Optional[str]:
    try:
        from src.core.auth_utils import safe_get
        user = st.session_state.get("user")
        uid = safe_get(user, "id")
        if uid and safe_get(user, "is_authenticated") and safe_get(user, "mode") != "local":
            return uid
    except Exception:
        pass
    return None


def _load_from_supabase() -> Optional[Dict[str, Any]]:
    uid = _user_id()
    if not uid:
        return None
    try:
        from src.core.supabase_client import SupabaseManager
        res = SupabaseManager().select("brand_profiles", filters={"user_id": uid})
        if res.get("status") == "success" and res.get("data"):
            return res["data"][0]
    except Exception:
        pass
    return None


def _save_to_supabase(profile: Dict[str, Any]) -> None:
    uid = _user_id()
    if not uid:
        return
    try:
        from src.core.supabase_client import SupabaseManager
        mgr = SupabaseManager()
        payload = {k: str(profile.get(k, "")) for k, _ in FIELDS}
        payload["user_id"] = uid
        payload["change_log"] = profile.get("change_log", [])
        payload["updated_at"] = profile.get("updated_at", "")
        existing = mgr.select("brand_profiles", filters={"user_id": uid})
        if existing.get("status") == "success" and existing.get("data"):
            mgr.update("brand_profiles", {"user_id": uid}, payload)
        else:
            mgr.insert("brand_profiles", payload)
    except Exception:
        pass
