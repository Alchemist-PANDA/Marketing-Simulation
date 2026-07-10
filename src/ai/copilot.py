"""
AI Marketing Copilot — DeepSeek-powered expert advisor.

Key changes vs. original:
  • Uses APIKeyManager (src/ai/key_manager.py) for automatic multi-key
    rotation.  When a key hits its quota the manager marks it exhausted
    and the next call retries with the next available key — transparently.
  • call_deepseek() now loops over all available keys before giving up,
    returning a user-friendly error if every key is exhausted.
  • Fully backward-compatible: a single DEEPSEEK_API_KEY still works.

Environment variables (add to .env or Streamlit secrets):
  DEEPSEEK_API_KEY_1=sk-...     # preferred: numbered keys
  DEEPSEEK_API_KEY_2=sk-...
  DEEPSEEK_API_KEYS=sk-a,sk-b   # alt: comma-separated
  DEEPSEEK_API_KEY=sk-...        # legacy: single key
  DEEPSEEK_BASE_URL=https://api.deepseek.com/v1  # optional override
"""
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st
from dotenv import load_dotenv

from .key_manager import APIKeyManager, is_quota_error

load_dotenv()

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior marketing advisor with deep expertise in:
- Digital advertising (Facebook, Google, TikTok, Instagram, email)
- Consumer psychology (Big Five / OCEAN personality traits, Prospect Theory)
- Brand strategy, creative optimization, and A/B testing
- Data-driven marketing analytics and campaign optimization
- DTC e-commerce, conversion rate optimization, and growth hacking

You provide detailed, actionable advice backed by data and reasoning.
When analyzing simulation results, reference specific metrics and explain WHY
certain patterns emerged based on the underlying consumer psychology model.
Keep responses concise but insightful. Use bullet points for actionable items.
Never fabricate statistics — only reference data the user has shared."""

# ── Module-level key manager (singleton per Streamlit session) ────────────────
# Instantiated here so it is shared across all copilot calls within a session.
_key_manager: Optional[APIKeyManager] = None


def _get_key_manager() -> APIKeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager(env_var_prefix="DEEPSEEK_API_KEY")
    return _key_manager


def _get_base_url() -> str:
    """Return the DeepSeek base URL from env / secrets."""
    url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    try:
        if "DEEPSEEK_BASE_URL" in st.secrets:
            url = st.secrets["DEEPSEEK_BASE_URL"]
    except Exception:
        pass
    return url


# ── Core API call with key rotation ──────────────────────────────────────────

def call_deepseek(
    messages: List[Dict[str, str]],
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float = 0.7,
    max_tokens: int = 1200,
) -> Dict[str, Any]:
    """
    Send a chat completion request to DeepSeek's API with automatic key rotation.

    Rotation behaviour:
      1. Get the next available key from the manager.
      2. Make the request.
      3. If the response signals quota exhaustion (HTTP 402, 429 + quota body),
         mark the key exhausted and retry with the next key.
      4. If the response signals a transient rate-limit (429 without quota body),
         mark the key rate-limited (recovers after COOLDOWN_SECONDS) and retry.
      5. If all keys fail, return a friendly error dict — never raises.

    Returns:
        {"status": "success", "content": "...", "key_label": "..."}
      or
        {"status": "error", "message": "...", "all_exhausted": bool}
    """
    km = _get_key_manager()
    base_url = _get_base_url()

    if km.key_count == 0:
        return {
            "status": "error",
            "message": (
                "No API key configured. Add DEEPSEEK_API_KEY (or numbered variants) "
                "to your .env or Streamlit secrets."
            ),
        }

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    # We loop over all available keys, not a fixed retry count, so that every
    # key gets exactly one chance per call.
    attempted_keys: set = set()

    while True:
        key = km.get_next_key()

        # No more keys to try
        if key is None or key in attempted_keys:
            logger.error("KeyManager: all %d key(s) exhausted or unavailable", km.key_count)
            return {
                "status": "error",
                "all_exhausted": True,
                "message": (
                    "⚠️ All AI service quotas are currently exhausted. "
                    "Please try again later, add more API keys, or upgrade your plan."
                ),
            }

        attempted_keys.add(key)
        label = km.get_key_label(key)
        logger.info("Copilot: attempting request with key %s", label)

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": full_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )

            # ── Quota / billing error ─────────────────────────────────────
            if resp.status_code in (402, 429):
                body = resp.text
                if is_quota_error(resp.status_code, body):
                    logger.warning(
                        "Copilot: key %s quota EXHAUSTED (HTTP %d) — rotating",
                        label, resp.status_code
                    )
                    km.mark_quota_exhausted(key)
                    continue  # try next key
                else:
                    # Temporary rate-limit (429 without quota signal)
                    logger.warning(
                        "Copilot: key %s rate-limited (HTTP %d) — rotating",
                        label, resp.status_code
                    )
                    km.mark_rate_limited(key)
                    continue  # try next key

            # ── Other HTTP error ──────────────────────────────────────────
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                return {
                    "status": "error",
                    "message": f"API error ({e.response.status_code}): {e.response.text[:300]}",
                }

            # ── Success ───────────────────────────────────────────────────
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("Copilot: success with key %s", label)
            return {
                "status": "success",
                "content": content,
                "key_label": label,
            }

        except httpx.ConnectError:
            return {
                "status": "error",
                "message": "Cannot connect to DeepSeek API. Check your network and API URL.",
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "message": "Request timed out. The AI service may be overloaded — please retry.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)[:300]}"}


# ── File content extraction ───────────────────────────────────────────────────

def extract_file_content(uploaded_file) -> str:
    """Extract text content from an uploaded file."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)

    if name.endswith(".csv"):
        import pandas as pd
        from io import BytesIO
        df = pd.read_csv(BytesIO(raw))
        return (
            f"CSV file '{uploaded_file.name}' ({len(df)} rows, {len(df.columns)} columns):\n\n"
            f"Columns: {', '.join(df.columns)}\n\nFirst 20 rows:\n{df.head(20).to_string()}"
        )

    if name.endswith((".xlsx", ".xls")):
        import pandas as pd
        from io import BytesIO
        df = pd.read_excel(BytesIO(raw))
        return (
            f"Excel file '{uploaded_file.name}' ({len(df)} rows):\n\n"
            f"Columns: {', '.join(df.columns)}\n\nFirst 20 rows:\n{df.head(20).to_string()}"
        )

    if name.endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            from io import BytesIO
            reader = PdfReader(BytesIO(raw))
            pages = [page.extract_text() or "" for page in reader.pages[:20]]
            text = "\n---PAGE BREAK---\n".join(pages)
            return f"PDF file '{uploaded_file.name}' ({len(reader.pages)} pages):\n\n{text[:8000]}"
        except ImportError:
            return f"[PDF file '{uploaded_file.name}' uploaded but PyPDF2 is not installed]"

    if name.endswith(".docx"):
        try:
            from docx import Document
            from io import BytesIO
            doc = Document(BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs)
            return f"Word document '{uploaded_file.name}':\n\n{text[:8000]}"
        except ImportError:
            return f"[Word file '{uploaded_file.name}' uploaded but python-docx is not installed]"

    if name.endswith((".txt", ".md", ".log")):
        text = raw.decode("utf-8", errors="replace")
        return f"Text file '{uploaded_file.name}':\n\n{text[:8000]}"

    if name.endswith((".json", ".jsonl")):
        text = raw.decode("utf-8", errors="replace")
        return f"JSON file '{uploaded_file.name}':\n\n{text[:8000]}"

    if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return f"[Image file '{uploaded_file.name}' uploaded — image analysis not available in text mode]"

    return f"[File '{uploaded_file.name}' uploaded — unsupported format for text extraction]"


# ── Context builder ───────────────────────────────────────────────────────────

def build_context_message(report: Optional[Dict[str, Any]] = None) -> str:
    """Build a context string from the current report for the system prompt."""
    if not report:
        return ""

    result_json = report if "ad_a" in report else report.get("result_json", {})
    ad_a = result_json.get("ad_a", {})
    ad_b = result_json.get("ad_b", {})

    parts = [
        "\n\n--- CURRENT SIMULATION REPORT CONTEXT ---",
        f"Winner: Ad {result_json.get('winner', '?')}",
        f"Lift: {result_json.get('lift_percentage', 0):.2f}%",
        f"Objective: {result_json.get('objective', 'N/A')}",
    ]

    if report.get("ad_a_text"):
        parts.append(f"Ad A text: {report['ad_a_text']}")
    if report.get("ad_b_text"):
        parts.append(f"Ad B text: {report['ad_b_text']}")

    for label, data in [("Ad A", ad_a), ("Ad B", ad_b)]:
        if data:
            analysis = data.get("analysis", {})
            parts.append(
                f"{label}: likes={data.get('likes', 0)}, "
                f"conversions={data.get('conversions', 0)}, "
                f"shares={data.get('shares', 0)}, "
                f"CTR={analysis.get('predicted_ctr', 'N/A')}, "
                f"CVR={analysis.get('predicted_cvr', 'N/A')}"
            )
            failures = analysis.get("failure_reasons", [])
            if failures:
                parts.append(f"  Failure reasons: {'; '.join(failures)}")

    parts.append("--- END REPORT CONTEXT ---")
    return "\n".join(parts)


# ── High-level entry point ────────────────────────────────────────────────────

def get_copilot_response(
    user_message: str,
    chat_history: List[Dict[str, str]],
    report_context: Optional[Dict[str, Any]] = None,
    file_context: str = "",
) -> Dict[str, Any]:
    """High-level copilot entry point. Builds context and calls DeepSeek with key rotation."""
    system = SYSTEM_PROMPT

    ctx = build_context_message(report_context)
    if ctx:
        system += ctx

    if file_context:
        system += f"\n\n--- UPLOADED FILE CONTENT ---\n{file_context}\n--- END FILE CONTENT ---"

    messages = chat_history + [{"role": "user", "content": user_message}]

    result = call_deepseek(messages, system_prompt=system)

    if result["status"] == "error":
        # If all keys are exhausted show a clear message without falling back to
        # the rule-based stub — the user needs to know about the quota state.
        if result.get("all_exhausted"):
            return {
                "status": "success",   # surface as a message, not a hard error
                "content": (
                    "🔑 **All AI service quotas are currently exhausted.**\n\n"
                    "The copilot tried all configured API keys and none had remaining quota. "
                    "Options:\n"
                    "- ⏳ Wait a few minutes and try again (rate-limits reset automatically)\n"
                    "- ➕ Add more API keys via `DEEPSEEK_API_KEY_2`, `DEEPSEEK_API_KEY_3` etc.\n"
                    "- 💳 Upgrade your DeepSeek account for higher quotas"
                ),
                "quota_exhausted": True,
            }
        return _fallback_response(user_message, report_context)

    return result


def get_key_status() -> List[Dict]:
    """Return the current key rotation status (safe for UI display — keys are masked)."""
    return _get_key_manager().status_summary()


def reset_key_rotation() -> None:
    """Reset all keys to active state (manual override for debugging)."""
    _get_key_manager().reset_all()


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _fallback_response(
    user_message: str, report_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Rule-based fallback when the API is unavailable (non-quota errors)."""
    msg = user_message.lower()

    if report_context:
        result_json = (
            report_context if "ad_a" in report_context
            else report_context.get("result_json", {})
        )
        winner = result_json.get("winner", "?")
        lift = result_json.get("lift_percentage", 0)
        return {
            "status": "success",
            "content": (
                f"Based on your simulation results, **Ad {winner}** outperformed with a "
                f"**{lift:.2f}%** lift. To get deeper AI-powered analysis, please configure "
                f"your DeepSeek API key in the environment settings.\n\n"
                f"💡 **Quick tips:**\n"
                f"- Review the failure reasons for the losing ad\n"
                f"- Test variations of the winning ad's key phrases\n"
                f"- Consider A/B testing on different channels"
            ),
            "fallback": True,
        }

    if any(w in msg for w in ["facebook", "meta", "instagram"]):
        return {
            "status": "success",
            "content": (
                "For Meta/Facebook advertising, focus on:\n"
                "- **Hook in 3 seconds** — lead with value or curiosity\n"
                "- **Social proof** — numbers, testimonials, trust badges\n"
                "- **Clear CTA** — one action per ad\n\n"
                "Configure your DeepSeek API key for personalized AI advice."
            ),
            "fallback": True,
        }

    return {
        "status": "success",
        "content": (
            "I'm the Marketing Copilot! I can help with:\n"
            "- 📊 Analyzing your simulation results\n"
            "- 💡 Ad copy optimization strategies\n"
            "- 🎯 Channel-specific recommendations\n"
            "- 📁 Analyzing uploaded marketing data\n\n"
            "⚠️ For full AI-powered responses, add your DeepSeek API key "
            "to `.env` or Streamlit secrets."
        ),
        "fallback": True,
    }
