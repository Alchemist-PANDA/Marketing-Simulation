"""
AI Marketing Copilot — DeepSeek-powered expert advisor.
Provides context-aware marketing advice, report analysis, and file understanding.
Falls back gracefully when the API key is missing.
"""
import os
import json
import httpx
import streamlit as st
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

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


def _get_api_config() -> tuple:
    """Return (base_url, api_key) from env/secrets."""
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    try:
        if "DEEPSEEK_API_KEY" in st.secrets:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
        if "DEEPSEEK_BASE_URL" in st.secrets:
            base_url = st.secrets["DEEPSEEK_BASE_URL"]
    except Exception:
        pass

    return base_url, api_key


def call_deepseek(
    messages: List[Dict[str, str]],
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float = 0.7,
    max_tokens: int = 1200,
) -> Dict[str, Any]:
    """Send a chat completion request to DeepSeek's API.

    Returns {"status": "success", "content": "..."} on success,
    or {"status": "error", "message": "..."} on failure.
    """
    base_url, api_key = _get_api_config()

    if not api_key:
        return {
            "status": "error",
            "message": "DeepSeek API key not configured. Add DEEPSEEK_API_KEY to your .env or Streamlit secrets.",
        }

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": full_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {"status": "success", "content": content}

    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": f"API error ({e.response.status_code}): {e.response.text[:300]}"}
    except httpx.ConnectError:
        return {"status": "error", "message": "Cannot connect to DeepSeek API. Check your network and API URL."}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)[:300]}"}


def extract_file_content(uploaded_file) -> str:
    """Extract text content from an uploaded file."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)

    if name.endswith(".csv"):
        import pandas as pd
        from io import BytesIO
        df = pd.read_csv(BytesIO(raw))
        return f"CSV file '{uploaded_file.name}' ({len(df)} rows, {len(df.columns)} columns):\n\nColumns: {', '.join(df.columns)}\n\nFirst 20 rows:\n{df.head(20).to_string()}"

    if name.endswith((".xlsx", ".xls")):
        import pandas as pd
        from io import BytesIO
        df = pd.read_excel(BytesIO(raw))
        return f"Excel file '{uploaded_file.name}' ({len(df)} rows):\n\nColumns: {', '.join(df.columns)}\n\nFirst 20 rows:\n{df.head(20).to_string()}"

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


def get_copilot_response(user_message: str, chat_history: List[Dict[str, str]],
                         report_context: Optional[Dict[str, Any]] = None,
                         file_context: str = "") -> Dict[str, Any]:
    """High-level copilot entry point. Builds context and calls DeepSeek."""
    system = SYSTEM_PROMPT

    # Add report context if available
    ctx = build_context_message(report_context)
    if ctx:
        system += ctx

    # Add file context if available
    if file_context:
        system += f"\n\n--- UPLOADED FILE CONTENT ---\n{file_context}\n--- END FILE CONTENT ---"

    messages = chat_history + [{"role": "user", "content": user_message}]

    result = call_deepseek(messages, system_prompt=system)

    if result["status"] == "error":
        return _fallback_response(user_message, report_context)

    return result


def _fallback_response(user_message: str, report_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Rule-based fallback when the API is unavailable."""
    msg = user_message.lower()

    if report_context:
        result_json = report_context if "ad_a" in report_context else report_context.get("result_json", {})
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
