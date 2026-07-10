"""
src/recommendation/engine.py
────────────────────────────
Generates improved ad copy variants using the Gemini API.

Was previously pointing at DeepSeek / OpenAI (openai SDK).
Now uses httpx + Gemini directly, consistent with the copilot.
"""
import json
import os

import httpx


def generate_ad_variants(
    ad_text: str, strengths: list, weaknesses: list, num_variants: int = 3
) -> list:
    """
    Call Gemini to generate improved ad variants based on weaknesses and strengths.
    Returns a list of dicts with keys: 'new_text', 'explanation', 'predicted_lift'.
    Returns [] on any failure so callers degrade gracefully.
    """
    # ── Resolve an API key ──────────────────────────────────────────────────
    api_key = ""
    for env_var in ("GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3",
                    "GEMINI_API_KEY"):
        api_key = os.environ.get(env_var, "").strip()
        if api_key:
            break

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
        return []

    # ── Build the prompt ────────────────────────────────────────────────────
    prompt = f"""You are an elite direct-response copywriter.
Below is an ad that was tested in our psychographic simulation engine.

**Original Ad:** "{ad_text}"

**Identified Strengths:** {', '.join(strengths) if strengths else 'None'}
**Identified Weaknesses:** {', '.join(weaknesses) if weaknesses else 'None'}

Your task is to generate {num_variants} improved variants of this ad.
For each variant, fix the weaknesses while amplifying the strengths.
Each variant should take a slightly different psychological angle (e.g., Urgency, Trust, Social Proof).

Provide the output strictly as a JSON array of objects, with each object having exactly these keys:
- "new_text": The rewritten ad copy.
- "explanation": A 1-sentence explanation of what changed and why it fixes the weaknesses.
- "predicted_lift": A string estimating the conversion lift (e.g., "+15%").

Return ONLY valid JSON array."""

    # ── Call Gemini ─────────────────────────────────────────────────────────
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": "You output strict JSON arrays."}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800},
    }

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(url, headers={"Content-Type": "application/json"},
                               json=payload)
        if resp.status_code != 200:
            print(f"Gemini API error {resp.status_code}: {resp.text[:200]}")
            return []

        data = resp.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]

        # Strip markdown fences if Gemini wraps the JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        variants = json.loads(content.strip())

        # Normalise if Gemini returned a dict wrapper instead of a bare list
        if isinstance(variants, dict):
            for v in variants.values():
                if isinstance(v, list):
                    variants = v
                    break

        if not isinstance(variants, list):
            variants = [variants]

        return variants

    except Exception as e:
        print(f"Error generating variants via Gemini: {e}")
        return []
