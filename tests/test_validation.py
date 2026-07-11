"""Unit tests for input validation (src/core/validation.py)."""
from src.core.validation import MIN_PASSWORD_LEN, sanitize_text, validate_email, validate_password


def test_valid_email():
    assert validate_email("user@example.com")[0] is True


def test_invalid_emails():
    for bad in ["", "no-at", "a@b", "a@b.", "@x.com", "x@.com", "spaces @x.com"]:
        assert validate_email(bad)[0] is False, bad


def test_password_too_short():
    ok, msg = validate_password("Ab1")
    assert ok is False and str(MIN_PASSWORD_LEN) in msg


def test_password_requires_letter_and_digit():
    assert validate_password("12345678")[0] is False   # no letter
    assert validate_password("abcdefgh")[0] is False    # no digit


def test_password_strong_enough():
    assert validate_password("Sunshine9")[0] is True


def test_sanitize_bounds_length():
    assert sanitize_text("x" * 10000, max_len=100) == "x" * 100
    assert sanitize_text(None) == ""
    assert sanitize_text("  hi  ") == "hi"
