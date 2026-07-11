"""
Input validation helpers — used by auth and any user-facing form.

Kept dependency-free and pure so they are trivially unit-testable.
"""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Minimum password policy (documented in CONTRIBUTING.md / README).
MIN_PASSWORD_LEN = 8


def validate_email(email: str) -> tuple[bool, str]:
    """Return (ok, message). Message is empty when ok."""
    if not email or not _EMAIL_RE.match(email.strip()):
        return False, "Please enter a valid email address."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Enforce a strong-enough password: length + letter + digit.

    Deliberately not over-strict (no forced symbols) to avoid harming usability,
    but strong enough to reject the common weak cases.
    """
    if password is None or len(password) < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""


def sanitize_text(text: str, max_len: int = 5000) -> str:
    """Trim and bound free-text input to guard against oversized payloads.

    Note: Streamlit renders user text as data (not HTML) by default, so this is
    a length/whitespace guard, not an HTML sanitizer. Never pass user text into
    st.markdown(..., unsafe_allow_html=True).
    """
    if text is None:
        return ""
    return str(text).strip()[:max_len]
