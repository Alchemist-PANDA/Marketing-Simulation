"""
src/ai/key_manager.py
─────────────────────
Multi-API-key rotation manager for the AI Marketing Copilot.

Currently configured for Google Gemini, but fully provider-agnostic —
the prefix can be overridden to support any API key naming convention.

Supports:
  • Numbered env vars:       GEMINI_API_KEY_1, GEMINI_API_KEY_2, …
  • Comma-separated list:    GEMINI_API_KEYS=key-aaa,key-bbb
  • Streamlit secrets:       GEMINI_API_KEY_1 / GEMINI_API_KEYS flat keys
  • Legacy single key:       GEMINI_API_KEY  (backward-compatible)

Each key entry tracks:
  • exhausted  – permanent quota exceeded (won't be retried until reset)
  • rate_limited – temporary rate-limit; re-enables after COOLDOWN_SECONDS
  • failure_count – consecutive failures on this key
  • last_failure – epoch timestamp of the most recent failure

Quota-signal detection (HTTP 429, 402, 403 or body containing
"quota", "RESOURCE_EXHAUSTED", "billing" etc.) marks the key exhausted.
Other transient errors mark it rate_limited and allow recovery after
COOLDOWN_SECONDS.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)

# ── tunables ────────────────────────────────────────────────────────────────
COOLDOWN_SECONDS: int = 60          # rate-limited keys recover after this
MAX_FAILURES_BEFORE_EXHAUST: int = 3  # consecutive non-quota failures → exhaust

# Keywords in an API response body that signal permanent quota exhaustion.
# Covers both DeepSeek/OpenAI style and Gemini style (RESOURCE_EXHAUSTED).
QUOTA_SIGNALS = frozenset(
    ["insufficient_quota", "quota_exceeded", "quota", "billing",
     "payment", "out of tokens", "exceeded your current quota",
     "resource_exhausted", "rateLimitExceeded", "dailylimitexceeded",
     "userRateLimitExceeded"]
)

# HTTP status codes that always mean "quota / billing" rather than transient error
QUOTA_STATUS_CODES = frozenset([402, 429])

# ── session-state key ────────────────────────────────────────────────────────
_SS_KEY = "_api_key_manager_state"


# ── internal helpers ─────────────────────────────────────────────────────────

def _blank_entry(key: str, label: str = "") -> Dict:
    return {
        "key": key,
        "label": label or f"key-{key[-6:]}",   # last 6 chars for logging
        "exhausted": False,
        "rate_limited": False,
        "failure_count": 0,
        "last_failure": 0.0,
    }


def _load_from_env(prefix: str = "GEMINI_API_KEY") -> List[Dict]:
    """Load keys from environment variables (numbered or comma-separated)."""
    entries: List[Dict] = []

    # 1) Numbered: GEMINI_API_KEY_1, GEMINI_API_KEY_2, …
    i = 1
    while True:
        k = os.getenv(f"{prefix}_{i}", "").strip()
        if not k:
            break
        entries.append(_blank_entry(k, label=f"env-{i}"))
        i += 1

    # 2) Comma-separated: GEMINI_API_KEYS=key-aaa,key-bbb
    if not entries:
        combined = os.getenv(f"{prefix}S", "").strip()  # e.g. GEMINI_API_KEYS
        if combined:
            for idx, k in enumerate(combined.split(","), 1):
                k = k.strip()
                if k:
                    entries.append(_blank_entry(k, label=f"env-csv-{idx}"))

    # 3) Legacy single key: GEMINI_API_KEY
    if not entries:
        k = os.getenv(prefix, "").strip()
        if k:
            entries.append(_blank_entry(k, label="env-legacy"))

    return entries


def _load_from_secrets(prefix: str = "GEMINI_API_KEY") -> List[Dict]:
    """Load keys from Streamlit secrets (various layouts)."""
    entries: List[Dict] = []
    try:
        secrets = st.secrets
    except Exception:
        return entries

    # Layout A: section with a list value → secrets["gemini_api_keys"] = ["key-a", …]
    section_name = prefix.lower().rstrip("_") + "s"   # e.g. "gemini_api_keys"
    # also try simpler aliases
    for sec in [section_name, "gemini_keys", "api_keys"]:
        try:
            val = secrets[sec]
            if isinstance(val, (list, tuple)):
                for idx, k in enumerate(val, 1):
                    k = str(k).strip()
                    if k:
                        entries.append(_blank_entry(k, label=f"secret-list-{idx}"))
                if entries:
                    return entries
        except (KeyError, Exception):
            pass

    # Layout B: GEMINI_API_KEY_1, GEMINI_API_KEY_2, … as flat secret keys
    i = 1
    while True:
        try:
            k = str(secrets[f"{prefix}_{i}"]).strip()
        except (KeyError, Exception):
            break
        if not k:
            break
        entries.append(_blank_entry(k, label=f"secret-{i}"))
        i += 1

    # Layout C: GEMINI_API_KEYS comma-separated flat secret
    if not entries:
        try:
            combined = str(secrets.get(f"{prefix}S", "")).strip()
            for idx, k in enumerate(combined.split(","), 1):
                k = k.strip()
                if k:
                    entries.append(_blank_entry(k, label=f"secret-csv-{idx}"))
        except Exception:
            pass

    # Layout D: legacy single flat key
    if not entries:
        try:
            k = str(secrets[prefix]).strip()
            if k:
                entries.append(_blank_entry(k, label="secret-legacy"))
        except (KeyError, Exception):
            pass

    return entries


# ── public API ───────────────────────────────────────────────────────────────

class APIKeyManager:
    """
    Thread-safe (single-process) key rotation manager.

    State is stored in st.session_state so it persists across Streamlit
    reruns within a single user session.  Instantiate once at module level;
    the Streamlit session will initialise it on first use.
    """

    def __init__(self, env_var_prefix: str = "GEMINI_API_KEY"):
        self._prefix = env_var_prefix
        # Ensure session state is initialised
        if _SS_KEY not in st.session_state:
            self._init_state()

    # ── state helpers ────────────────────────────────────────────────────────

    def _init_state(self) -> None:
        """Populate st.session_state with keys from env + secrets."""
        entries: List[Dict] = []

        # secrets take priority over env vars (Streamlit Cloud deployment)
        secret_entries = _load_from_secrets(self._prefix)
        env_entries = _load_from_env(self._prefix)

        # Deduplicate by key value (secrets may duplicate env)
        seen: set = set()
        for e in secret_entries + env_entries:
            if e["key"] not in seen:
                seen.add(e["key"])
                entries.append(e)

        st.session_state[_SS_KEY] = entries
        logger.info("KeyManager: loaded %d key(s)", len(entries))

    @property
    def _state(self) -> List[Dict]:
        if _SS_KEY not in st.session_state:
            self._init_state()
        return st.session_state[_SS_KEY]

    # ── public methods ───────────────────────────────────────────────────────

    @property
    def key_count(self) -> int:
        return len(self._state)

    @property
    def available_count(self) -> int:
        now = time.time()
        return sum(1 for e in self._state if self._is_available(e, now))

    def _is_available(self, entry: Dict, now: float) -> bool:
        if entry["exhausted"]:
            return False
        if entry["rate_limited"]:
            # auto-recover after cooldown
            if now - entry["last_failure"] >= COOLDOWN_SECONDS:
                entry["rate_limited"] = False
                entry["failure_count"] = 0
                logger.info("KeyManager: key %s recovered from rate-limit", entry["label"])
                return True
            return False
        return True

    def get_next_key(self) -> Optional[str]:
        """Return the next available key, or None if all are exhausted."""
        now = time.time()
        for entry in self._state:
            if self._is_available(entry, now):
                logger.debug("KeyManager: using key %s", entry["label"])
                return entry["key"]
        return None

    def get_key_label(self, key: str) -> str:
        """Return the human-readable label for a key (for logging)."""
        for e in self._state:
            if e["key"] == key:
                return e["label"]
        return "unknown"

    def mark_quota_exhausted(self, key: str) -> None:
        """Permanently mark a key as quota-exceeded (billing / hard quota)."""
        for e in self._state:
            if e["key"] == key:
                e["exhausted"] = True
                e["failure_count"] += 1
                e["last_failure"] = time.time()
                logger.warning(
                    "KeyManager: key %s marked EXHAUSTED (quota)", e["label"]
                )
                break

    def mark_rate_limited(self, key: str) -> None:
        """Temporarily mark a key as rate-limited; it will recover after COOLDOWN."""
        for e in self._state:
            if e["key"] == key:
                e["rate_limited"] = True
                e["failure_count"] += 1
                e["last_failure"] = time.time()
                # After enough consecutive rate-limits, treat as exhausted
                if e["failure_count"] >= MAX_FAILURES_BEFORE_EXHAUST:
                    e["exhausted"] = True
                    logger.warning(
                        "KeyManager: key %s permanently exhausted after %d failures",
                        e["label"], e["failure_count"]
                    )
                else:
                    logger.warning(
                        "KeyManager: key %s rate-limited (failure %d/%d)",
                        e["label"], e["failure_count"], MAX_FAILURES_BEFORE_EXHAUST
                    )
                break

    def reset_all(self) -> None:
        """Un-exhaust all keys (useful for testing or manual reset)."""
        for e in self._state:
            e["exhausted"] = False
            e["rate_limited"] = False
            e["failure_count"] = 0
        logger.info("KeyManager: all keys reset")

    def status_summary(self) -> List[Dict]:
        """Return a sanitised status list (keys are masked) for UI display."""
        now = time.time()
        out = []
        for e in self._state:
            if e["exhausted"]:
                state = "❌ exhausted"
            elif e["rate_limited"]:
                remaining = max(0, int(COOLDOWN_SECONDS - (now - e["last_failure"])))
                state = f"⏳ rate-limited ({remaining}s)"
            else:
                state = "✅ active"
            out.append({"label": e["label"], "status": state,
                        "failures": e["failure_count"]})
        return out


def is_quota_error(status_code: int, body: str) -> bool:
    """Return True if the error signals permanent quota exhaustion."""
    if status_code in QUOTA_STATUS_CODES:
        body_lower = body.lower()
        # 429 can be temporary rate-limit OR quota; check body for quota signals
        if status_code == 429:
            return any(sig in body_lower for sig in QUOTA_SIGNALS)
        # 402 (payment required) is always a quota/billing issue
        return True
    body_lower = body.lower()
    return any(sig in body_lower for sig in QUOTA_SIGNALS)
