"""
src/utils/ai_reasoning.py
─────────────────────────
Generates narrative AI insights from A/B simulation results using the
Gemini API (via the shared APIKeyManager for multi-key rotation).

Was previously pointing at DeepSeek via the openai SDK.  Now uses
httpx + Gemini directly, consistent with the rest of the copilot.
"""
import os
from typing import Any, Dict, Optional

import httpx


def get_ai_insights(
    result: Dict[str, Any],
    ad_a_text: str,
    ad_b_text: str,
    benchmarks: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Call Gemini to generate a rich narrative based on simulation data.
    Returns the insights string, or a friendly fallback message on failure.
    """
    # ── Resolve an API key (try the same numbered pattern as the copilot) ──
    api_key = ""
    for env_var in ("GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3",
                    "GEMINI_API_KEY"):
        api_key = os.environ.get(env_var, "").strip()
        if api_key:
            break

    # Also try Streamlit secrets if running on Cloud
    if not api_key:
        try:
            import streamlit as st
            for key_name in ("GEMINI_API_KEY_1", "GEMINI_API_KEY_2",
                             "GEMINI_API_KEY_3", "GEMINI_API_KEY"):
                api_key = str(st.secrets.get(key_name, "")).strip()
                if api_key:
                    break
        except Exception:
            pass

    if not api_key:
        return (
            "AI insights temporarily unavailable. "
            "Add your GEMINI_API_KEY (or GEMINI_API_KEY_1 / _2 / _3) "
            "to your .env or Streamlit secrets."
        )

    # ── Build the prompt ────────────────────────────────────────────────────
    total_agents = result["ad_a"].get("total_agents", 0)
    ad_a = result["ad_a"]
    ad_b = result["ad_b"]

    def safe_get(d, *keys, default=0):
        for k in keys:
            if not isinstance(d, dict):
                return default
            d = d.get(k, default)
        return d

    prompt = f"""You are a senior marketing analyst. Below is the output of an A/B test simulation on {total_agents} agents. The simulation models consumer psychology using OCEAN personality traits and Prospect Theory.

**Ad A:** {ad_a_text}
**Ad B:** {ad_b_text}

**Metrics:**

| Metric | Ad A | Ad B |
|--------|------|------|
| Conversion Rate | {ad_a.get('conversion_rate', 0)}% | {ad_b.get('conversion_rate', 0)}% |
| Engagement Rate | {ad_a.get('engagement_rate', 0)}% | {ad_b.get('engagement_rate', 0)}% |
| Trust Score | {safe_get(ad_a, 'scores', 'trust', default=0)} | {safe_get(ad_b, 'scores', 'trust', default=0)} |
| Urgency Score | {safe_get(ad_a, 'scores', 'urgency', default=0)} | {safe_get(ad_b, 'scores', 'urgency', default=0)} |
| Openness Resonance | {safe_get(ad_a, 'personality_performance', 'openness', default=0)} | {safe_get(ad_b, 'personality_performance', 'openness', default=0)} |
| Perceived Value | {safe_get(ad_a, 'prospect_insights', 'perceived_value', default=0)} | {safe_get(ad_b, 'prospect_insights', 'perceived_value', default=0)} |
| Loss Aversion Impact | {safe_get(ad_a, 'prospect_insights', 'loss_aversion_impact', default=0)} | {safe_get(ad_b, 'prospect_insights', 'loss_aversion_impact', default=0)} |

**Segmentation:** Low-income conversion: {safe_get(ad_a, 'segment_analysis', 'low_income', 'conversion_rate', default=0)}% vs {safe_get(ad_b, 'segment_analysis', 'low_income', 'conversion_rate', default=0)}%.

**Industry benchmarks:** {benchmarks or "None provided"}.

Please provide:
1. **Winner summary** – Who won and why, in 2 sentences.
2. **Deep analysis** – Strengths and weaknesses of each ad, linked to data.
3. **Creative recommendations** – Specific copy or design changes, with estimated impact.
4. **Market context** – How do these results compare to current trends? (Use benchmarks if provided.)
5. **Future outlook** – What can we expect if we apply these changes?

Be concise, data-driven, and avoid generic advice. Use bullet points and bold text for emphasis."""

    # ── Call Gemini ─────────────────────────────────────────────────────────
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {
            "parts": [{"text": "You are a senior data-driven marketing analyst."}]
        },
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
    }

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(url, headers={"Content-Type": "application/json"},
                               json=payload)
        if resp.status_code != 200:
            return (
                f"AI insights temporarily unavailable "
                f"(Gemini API error {resp.status_code}). Please try again later."
            )
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"AI insights temporarily unavailable. Please try again later. (Error: {str(e)[:200]})"
