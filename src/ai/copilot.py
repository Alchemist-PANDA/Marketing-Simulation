"""
AI Marketing Copilot — Gemini-powered expert advisor.

Uses Google's Gemini API (generativelanguage.googleapis.com) with the
same multi-key rotation system (APIKeyManager) built in key_manager.py.

Authentication differs from OpenAI-compatible APIs:
  • Gemini uses a query-parameter key (?key=…) not a Bearer header.
  • Request body uses "contents" / "parts" format instead of "messages".
  • System instructions go in a separate "system_instruction" field.
  • Role names are "user" and "model" (not "assistant").

Environment variables (add to .env or Streamlit secrets):
  GEMINI_API_KEY_1=AIza...    # preferred: numbered keys
  GEMINI_API_KEY_2=AIza...
  GEMINI_API_KEY_3=AIza...
  GEMINI_API_KEYS=AIza...,AIza...   # alt: comma-separated
  GEMINI_API_KEY=AIza...             # legacy: single key (backward-compat)
  GEMINI_MODEL=gemini-1.5-flash      # optional model override
"""
from __future__ import annotations

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

# ── Gemini API settings ───────────────────────────────────────────────────────
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_DEFAULT_MODEL = "gemini-1.5-flash"   # free-tier friendly, fast


def _get_gemini_model() -> str:
    """Return the Gemini model name from env / secrets."""
    model = os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)
    try:
        if "GEMINI_MODEL" in st.secrets:
            model = st.secrets["GEMINI_MODEL"]
    except Exception:
        pass
    return model


def _gemini_endpoint(api_key: str) -> str:
    """Build the full Gemini generateContent URL with key query param."""
    model = _get_gemini_model()
    return f"{_GEMINI_BASE}/{model}:generateContent?key={api_key}"


# ── Module-level key manager (singleton per Streamlit session) ────────────────
_key_manager: Optional[APIKeyManager] = None


def _get_key_manager() -> APIKeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager(env_var_prefix="GEMINI_API_KEY")
    return _key_manager


# ── Message format conversion ─────────────────────────────────────────────────

def _to_gemini_contents(
    messages: List[Dict[str, str]],
) -> List[Dict]:
    """
    Convert OpenAI-style messages to Gemini 'contents' format.

    OpenAI:  [{"role": "user"|"assistant", "content": "..."}]
    Gemini:  [{"role": "user"|"model",     "parts": [{"text": "..."}]}]
    """
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        # Gemini uses "model" for assistant turns
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({
            "role": gemini_role,
            "parts": [{"text": msg.get("content", "")}],
        })
    return contents


# ── Core API call with key rotation ──────────────────────────────────────────

def call_gemini(
    messages: List[Dict[str, str]],
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float = 0.7,
    max_tokens: int = 1200,
) -> Dict[str, Any]:
    """
    Send a chat completion request to Gemini with automatic key rotation.

    Rotation behaviour:
      1. Get the next available key from the manager.
      2. POST to generateContent with the key as a query parameter.
      3. HTTP 429 with RESOURCE_EXHAUSTED / quota body → mark exhausted, retry.
      4. HTTP 429 (plain rate-limit) → mark rate-limited (recovers after cooldown), retry.
      5. All keys tried → return friendly error dict, never raises.

    Returns:
        {"status": "success", "content": "...", "key_label": "..."}
      or
        {"status": "error", "message": "...", "all_exhausted": bool}
    """
    km = _get_key_manager()

    if km.key_count == 0:
        return {
            "status": "error",
            "no_keys": True,
            "message": (
                "No Gemini API key configured. Add GEMINI_API_KEY (or numbered "
                "variants GEMINI_API_KEY_1 / GEMINI_API_KEY_2 …) to your .env "
                "or Streamlit secrets."
            ),
        }

    # Build Gemini payload
    contents = _to_gemini_contents(messages)
    payload: Dict[str, Any] = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "candidateCount": 1,
        },
    }

    attempted_keys: set = set()

    while True:
        key = km.get_next_key()

        if key is None or key in attempted_keys:
            logger.error("Gemini KeyManager: all %d key(s) exhausted", km.key_count)
            return {
                "status": "error",
                "all_exhausted": True,
                "message": (
                    "⚠️ All Gemini API quotas are currently exhausted. "
                    "Please try again later, add more API keys, or upgrade your plan."
                ),
            }

        attempted_keys.add(key)
        label = km.get_key_label(key)
        url = _gemini_endpoint(key)
        logger.info("Copilot: attempting Gemini request with key %s", label)

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )

            # ── Quota / billing error ────────────────────────────────────
            if resp.status_code in (429, 402, 403):
                body = resp.text
                if is_quota_error(resp.status_code, body):
                    logger.warning(
                        "Copilot: key %s quota EXHAUSTED (HTTP %d) — rotating",
                        label, resp.status_code,
                    )
                    km.mark_quota_exhausted(key)
                    continue
                else:
                    logger.warning(
                        "Copilot: key %s rate-limited (HTTP %d) — rotating",
                        label, resp.status_code,
                    )
                    km.mark_rate_limited(key)
                    continue

            # ── Other HTTP error ─────────────────────────────────────────
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                return {
                    "status": "error",
                    "message": (
                        f"Gemini API error ({e.response.status_code}): "
                        f"{e.response.text[:300]}"
                    ),
                }

            # ── Parse Gemini response ────────────────────────────────────
            data = resp.json()
            try:
                content = (
                    data["candidates"][0]["content"]["parts"][0]["text"]
                )
            except (KeyError, IndexError) as parse_err:
                # Gemini occasionally returns finishReason=SAFETY with no text
                finish = (
                    data.get("candidates", [{}])[0]
                    .get("finishReason", "UNKNOWN")
                )
                logger.warning(
                    "Copilot: key %s response parse error (%s), finishReason=%s",
                    label, parse_err, finish,
                )
                return {
                    "status": "error",
                    "message": (
                        f"Gemini returned an empty response (finishReason={finish}). "
                        "The prompt may have triggered a safety filter."
                    ),
                }

            logger.info("Copilot: Gemini success with key %s", label)
            return {
                "status": "success",
                "content": content,
                "key_label": label,
            }

        except httpx.ConnectError:
            return {
                "status": "error",
                "message": "Cannot connect to Gemini API. Check your network connection.",
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "message": "Request timed out. The Gemini service may be overloaded — please retry.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)[:300]}"}


# Legacy alias — kept so any external callers of call_deepseek() don't break.
# New code should call call_gemini() directly.
call_deepseek = call_gemini


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
    """High-level copilot entry point. Builds context and calls Gemini with key rotation."""
    system = SYSTEM_PROMPT

    ctx = build_context_message(report_context)
    if ctx:
        system += ctx

    if file_context:
        system += f"\n\n--- UPLOADED FILE CONTENT ---\n{file_context}\n--- END FILE CONTENT ---"

    messages = chat_history + [{"role": "user", "content": user_message}]

    result = call_gemini(messages, system_prompt=system)

    if result["status"] == "error":
        if result.get("all_exhausted"):
            return {
                "status": "success",   # surface as a message, not a hard crash
                "content": (
                    "🔑 **All Gemini API quotas are currently exhausted.**\n\n"
                    "The copilot tried all configured API keys and none had remaining quota. "
                    "Options:\n"
                    "- ⏳ Wait a few minutes and try again (rate-limits reset automatically)\n"
                    "- ➕ Add more keys via `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3` etc.\n"
                    "- 💳 Upgrade your Google AI Studio account for higher quotas"
                ),
                "quota_exhausted": True,
            }
        # Distinguish "no keys configured" (user action needed) from a transient
        # API/network error (keys exist but the call failed) so the UI banner is
        # accurate instead of always telling the user to add keys.
        reason = "no_keys" if result.get("no_keys") else "api_error"
        return _fallback_response(user_message, report_context, reason=reason)

    return result


def get_key_status() -> List[Dict]:
    """Return the current key rotation status (safe for UI — keys are masked)."""
    return _get_key_manager().status_summary()


def reset_key_rotation() -> None:
    """Reset all keys to active state (manual override for debugging)."""
    _get_key_manager().reset_all()


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _fallback_response(
    user_message: str,
    report_context: Optional[Dict[str, Any]] = None,
    reason: str = "no_keys",
) -> Dict[str, Any]:
    """Rule-based fallback when the API is unavailable.

    `reason` is either "no_keys" (no Gemini key configured — the user should add
    one) or "api_error" (keys exist but the request failed — a transient/service
    issue, so telling the user to add keys would be wrong). It is surfaced to the
    UI as `fallback_reason` so the banner can be accurate.
    """
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
                f"**{lift:.2f}%** lift.\n\n"
                f"💡 **Quick tips:**\n"
                f"- Review the failure reasons for the losing ad\n"
                f"- Test variations of the winning ad's key phrases\n"
                f"- Consider A/B testing on different channels"
            ),
            "fallback": True,
            "fallback_reason": reason,
        }

    if any(w in msg for w in ["facebook", "meta", "instagram"]):
        return {
            "status": "success",
            "content": (
                "For Meta/Facebook advertising, focus on:\n"
                "- **Hook in 3 seconds** — lead with value or curiosity\n"
                "- **Social proof** — numbers, testimonials, trust badges\n"
                "- **Clear CTA** — one action per ad"
            ),
            "fallback": True,
            "fallback_reason": reason,
        }

    return {
        "status": "success",
        "content": (
            "I'm the Marketing Copilot! I can help with:\n"
            "- 📊 Analyzing your simulation results\n"
            "- 💡 Ad copy optimization strategies\n"
            "- 🎯 Channel-specific recommendations\n"
            "- 📁 Analyzing uploaded marketing data"
        ),
        "fallback": True,
        "fallback_reason": reason,
    }
