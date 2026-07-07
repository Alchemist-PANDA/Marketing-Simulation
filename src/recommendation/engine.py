import os
import json

def generate_ad_variants(ad_text: str, strengths: list, weaknesses: list, num_variants: int = 3) -> list:
    """
    Calls DeepSeek/OpenAI to generate improved ad variants based on weaknesses and strengths.
    Returns a list of dictionaries with keys: 'new_text', 'explanation', 'predicted_lift'
    """
    try:
        from openai import OpenAI
    except ImportError:
        return []
        
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []

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

Return ONLY valid JSON array.
"""
    try:
        base_url = "https://api.deepseek.com" if "DEEPSEEK_API_KEY" in os.environ else None
        model = "deepseek-chat" if base_url else "gpt-4o-mini"
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You output strict JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        content = response.choices[0].message.content
        
        # Try to parse json, stripping markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        variants = json.loads(content.strip())
        
        # Normalize if it returned a dict wrapper
        if isinstance(variants, dict):
            for k in variants.keys():
                if isinstance(variants[k], list):
                    variants = variants[k]
                    break
                    
        if not isinstance(variants, list):
            variants = [variants]
            
        return variants
    except Exception as e:
        print(f"Error generating variants: {e}")
        return []
