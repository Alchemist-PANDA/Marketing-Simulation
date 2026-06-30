import os
from typing import Dict, Any, Optional

def get_ai_insights(result: Dict[str, Any], ad_a_text: str, ad_b_text: str, benchmarks: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Calls an LLM (e.g., OpenAI GPT-4o-mini) to generate a rich narrative based on the simulation data.
    Returns the generated insights as a string, or None if the call fails.
    """
    # Check if OpenAI is available
    try:
        from openai import OpenAI
    except ImportError:
        return "AI insights temporarily unavailable. Please install the `openai` package."
        
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "AI insights temporarily unavailable. DEEPSEEK_API_KEY environment variable is not set."

    # Extract relevant data
    total_agents = result['ad_a'].get('total_agents', 0)
    ad_a = result['ad_a']
    ad_b = result['ad_b']
    
    # Safely get deeply nested properties
    def safe_get(d, *keys, default=0):
        for k in keys:
            if not isinstance(d, dict): return default
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

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a senior data-driven marketing analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        # Graceful fallback on API failure
        return f"AI insights temporarily unavailable. Please try again later. (Error: {str(e)})"
