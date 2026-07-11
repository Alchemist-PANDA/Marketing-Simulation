"""
Lightweight health check for critical dependencies.

Streamlit has no HTTP routing, so a true ``/health`` endpoint isn't available;
instead ``health_check()`` returns a structured status dict that the app exposes
via the ``?health=1`` query parameter (see app.py) for uptime monitors and for
quick operator debugging.
"""
from __future__ import annotations

import os

from src.core.logging_config import get_logger, report_error

logger = get_logger(__name__)


def _check_supabase() -> dict:
    url = os.getenv("SUPABASE_URL") or _secret("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or _secret("SUPABASE_ANON_KEY")
    ok = bool(url and key)
    return {"ok": ok, "detail": "configured" if ok else "missing SUPABASE_URL / SUPABASE_ANON_KEY"}


def _check_models() -> dict:
    required = ["models/ensemble_model.pkl", "models/scaler.pkl"]
    missing = [p for p in required if not os.path.exists(p)]
    return {"ok": not missing, "detail": "present" if not missing else f"missing: {missing}"}


def _check_ai_key() -> dict:
    # Copilot degrades gracefully without a key, so this is informational only.
    key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("GEMINI_API_KEY") or _secret("GEMINI_API_KEY")
    return {"ok": True, "detail": "configured" if key else "absent (copilot runs in fallback mode)"}


def _secret(name: str):
    try:
        import streamlit as st
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None


def health_check() -> dict:
    """Return {status, checks{...}}. status is 'ok' unless a critical check fails."""
    checks = {}
    try:
        checks["database"] = _check_supabase()
        checks["models"] = _check_models()
        checks["ai_copilot"] = _check_ai_key()
    except Exception as exc:  # pragma: no cover
        eid = report_error(logger, exc, "health_check")
        return {"status": "error", "error_id": eid, "checks": checks}

    # Only the database is treated as critical for overall status.
    critical_ok = checks["database"]["ok"]
    return {"status": "ok" if critical_ok else "degraded", "checks": checks}
