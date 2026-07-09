"""
AI Marketing Copilot – Backend logic.
Provides context-aware marketing advice via the OpenAI-compatible API
(supports DeepSeek, OpenAI, etc.).
"""
from __future__ import annotations

import os
from typing import Optional

# ---------------------------------------------------------------------------
# Simple HTTP-based chat completion (no heavy SDK required)
# ---------------------------------------------------------------------------
import json
import urllib.request


_SYSTEM_PROMPT = """You are a world-class AI Marketing Copilot embedded inside a
marketing simulation platform. You help users:
• Craft high-converting ad copy for Facebook, TikTok, Instagram, Google, and Email
• Understand their simulation results (CTR, CVR, engagement lift, etc.)
• Optimise A/B test strategies and campaign budgets
• Interpret Big-Five personality-based audience segments
• Apply Prospect Theory insights to pricing and offers

Be concise, action-oriented, and data-driven. When the user shares simulation
numbers, analyse them and give specific, quantifiable recommendations."""


def _get_api_config() -> dict:
    """Return the API URL and key from environment / Streamlit secrets."""
    # Try Streamlit secrets first (cloud deployment)
    try:
        import streamlit as st
        api_key = st.secrets.get("DEEPSEEK_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
        base_url = st.secrets.get("AI_API_BASE_URL", "https://api.openai.com/v1")
        model = st.secrets.get("AI_MODEL", "gpt-3.5-turbo")
    except Exception:
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("AI_MODEL", "gpt-3.5-turbo")

    return {"api_key": api_key, "base_url": base_url.rstrip("/"), "model": model}


def chat(
    messages: list[dict],
    extra_context: Optional[str] = None,
    max_tokens: int = 600,
) -> str:
    """
    Send a chat request and return the assistant's reply as a string.

    Args:
        messages: List of {"role": "user"|"assistant", "content": str} dicts.
        extra_context: Additional context injected into the system prompt
                       (e.g. simulation results pasted by the user).
        max_tokens: Maximum tokens in the completion.

    Returns:
        The assistant reply string, or an error message prefixed with "❌".
    """
    cfg = _get_api_config()

    if not cfg["api_key"]:
        return (
            "❌ No API key found. Please add `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` "
            "to your Streamlit Cloud Secrets to enable the AI Copilot."
        )

    system_content = _SYSTEM_PROMPT
    if extra_context:
        system_content += f"\n\n--- Simulation Context ---\n{extra_context}"

    payload = {
        "model": cfg["model"],
        "messages": [{"role": "system", "content": system_content}] + messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    url = f"{cfg['base_url']}/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return f"❌ API error {e.code}: {body[:300]}"
    except Exception as exc:
        return f"❌ Request failed: {exc}"
