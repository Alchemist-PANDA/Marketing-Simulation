"""
tests/test_key_rotation.py
──────────────────────────
Unit tests for the APIKeyManager rotation logic.

Run with:  python -m pytest tests/test_key_rotation.py -v
Or:        python tests/test_key_rotation.py  (no pytest needed)
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# ── Minimal Streamlit session_state mock so we can test outside Streamlit ──
_ss = {}

class _FakeSS(dict):
    def __contains__(self, item):
        return super().__contains__(item)

_fake_ss = _FakeSS()

import types
st_mock = types.ModuleType("streamlit")
st_mock.session_state = _fake_ss
st_mock.secrets = {}
sys.modules["streamlit"] = st_mock

# Now import the module under test
from src.ai.key_manager import (
    APIKeyManager,
    COOLDOWN_SECONDS,
    MAX_FAILURES_BEFORE_EXHAUST,
    is_quota_error,
    _SS_KEY,
)


class TestIsQuotaError(unittest.TestCase):
    def test_402_always_quota(self):
        self.assertTrue(is_quota_error(402, "payment required"))

    def test_429_with_quota_body(self):
        self.assertTrue(is_quota_error(429, '{"error": "insufficient_quota"}'))

    def test_429_without_quota_body(self):
        self.assertFalse(is_quota_error(429, '{"error": "Too Many Requests"}'))

    def test_200_with_quota_body(self):
        # HTTP 200 with quota signal in body: is_quota_error checks body keywords
        # regardless of status code when non-quota status codes are involved.
        # The function correctly returns True here because the body contains a quota signal.
        self.assertTrue(is_quota_error(200, "insufficient_quota"))

    def test_500_no_quota(self):
        self.assertFalse(is_quota_error(500, "internal server error"))


class TestKeyManagerLoading(unittest.TestCase):
    def setUp(self):
        _fake_ss.clear()

    def test_numbered_keys(self):
        with patch.dict(os.environ, {
            "DEEPSEEK_API_KEY_1": "sk-one",
            "DEEPSEEK_API_KEY_2": "sk-two",
            "DEEPSEEK_API_KEY_3": "sk-three",
        }, clear=False):
            km = APIKeyManager()
            self.assertEqual(km.key_count, 3)
            self.assertEqual(km.available_count, 3)

    def test_csv_keys(self):
        _fake_ss.clear()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEYS": "sk-a,sk-b"}, clear=False):
            # Remove numbered keys that might leak in
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith("DEEPSEEK_API_KEY_")}
            env["DEEPSEEK_API_KEYS"] = "sk-a,sk-b"
            # Patch env entirely
            with patch.dict(os.environ, env, clear=True):
                km = APIKeyManager()
                self.assertGreaterEqual(km.key_count, 2)

    def test_legacy_single_key(self):
        _fake_ss.clear()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-legacy"}, clear=True):
            km = APIKeyManager()
            self.assertEqual(km.key_count, 1)
            self.assertEqual(km.get_next_key(), "sk-legacy")

    def test_no_keys(self):
        _fake_ss.clear()
        with patch.dict(os.environ, {}, clear=True):
            km = APIKeyManager()
            self.assertEqual(km.key_count, 0)
            self.assertIsNone(km.get_next_key())


class TestRotationLogic(unittest.TestCase):
    def _make_km(self, *keys) -> APIKeyManager:
        _fake_ss.clear()
        with patch.dict(os.environ, {}, clear=True):
            km = APIKeyManager()
            km._init_state()
            # Manually populate state
            _fake_ss[_SS_KEY] = [
                {"key": k, "label": f"test-{i}",
                 "exhausted": False, "rate_limited": False,
                 "failure_count": 0, "last_failure": 0.0}
                for i, k in enumerate(keys, 1)
            ]
            return km

    def test_first_key_returned(self):
        km = self._make_km("sk-one", "sk-two", "sk-three")
        self.assertEqual(km.get_next_key(), "sk-one")

    def test_exhausted_key_skipped(self):
        km = self._make_km("sk-one", "sk-two", "sk-three")
        km.mark_quota_exhausted("sk-one")
        self.assertEqual(km.get_next_key(), "sk-two")

    def test_all_exhausted_returns_none(self):
        km = self._make_km("sk-one", "sk-two")
        km.mark_quota_exhausted("sk-one")
        km.mark_quota_exhausted("sk-two")
        self.assertIsNone(km.get_next_key())

    def test_rate_limited_recovers_after_cooldown(self):
        km = self._make_km("sk-one", "sk-two")
        km.mark_rate_limited("sk-one")
        # Immediately: sk-one should be unavailable
        self.assertEqual(km.get_next_key(), "sk-two")
        # Simulate cooldown elapsed
        _fake_ss[_SS_KEY][0]["last_failure"] = time.time() - COOLDOWN_SECONDS - 1
        self.assertEqual(km.get_next_key(), "sk-one")

    def test_too_many_rate_limits_exhausts_key(self):
        km = self._make_km("sk-one", "sk-two")
        for _ in range(MAX_FAILURES_BEFORE_EXHAUST):
            # Each mark_rate_limited increments failure_count
            km.mark_rate_limited("sk-one")
            # Reset rate_limited flag so it doesn't interfere with count test
            _fake_ss[_SS_KEY][0]["rate_limited"] = False
        self.assertTrue(_fake_ss[_SS_KEY][0]["exhausted"])

    def test_reset_all(self):
        km = self._make_km("sk-one", "sk-two", "sk-three")
        km.mark_quota_exhausted("sk-one")
        km.mark_quota_exhausted("sk-two")
        km.reset_all()
        self.assertEqual(km.available_count, 3)

    def test_status_summary_masks_keys(self):
        km = self._make_km("sk-one")
        summary = km.status_summary()
        self.assertEqual(len(summary), 1)
        self.assertNotIn("sk-one", str(summary))   # key value not exposed
        self.assertIn("status", summary[0])


class TestSimulatedRotation(unittest.TestCase):
    """Simulate the exact sequence call_deepseek uses."""

    def test_rotation_on_quota(self):
        _fake_ss.clear()
        with patch.dict(os.environ, {}, clear=True):
            km = APIKeyManager()
        _fake_ss[_SS_KEY] = [
            {"key": "sk-bad",  "label": "bad",  "exhausted": False,
             "rate_limited": False, "failure_count": 0, "last_failure": 0.0},
            {"key": "sk-good", "label": "good", "exhausted": False,
             "rate_limited": False, "failure_count": 0, "last_failure": 0.0},
        ]

        used_keys = []
        attempted = set()

        while True:
            key = km.get_next_key()
            if key is None or key in attempted:
                break
            attempted.add(key)
            used_keys.append(key)
            if key == "sk-bad":
                km.mark_quota_exhausted(key)
                continue
            # sk-good succeeds
            break

        self.assertEqual(used_keys, ["sk-bad", "sk-good"])
        self.assertEqual(km.get_next_key(), "sk-good")  # sk-good still active


if __name__ == "__main__":
    print("=" * 60)
    print("APIKeyManager rotation test suite")
    print("=" * 60)
    unittest.main(verbosity=2)
