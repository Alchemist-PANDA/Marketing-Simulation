"""
Feature extraction and scoring module for marketing simulation.
Converts raw ad attributes and text into normalized scores (0-1).
"""

import re
from typing import Dict, Any

def extract_scores(ad_data: Dict[str, Any],
                   price_scale: float = 50.0) -> Dict[str, float]:
    """
    Extract normalized scores from raw ad data and text.
    Uses regex and heuristics to score price, trust, and urgency.
    """
    text = ad_data.get('text', '').lower()
    
    target_interest = None
    import re
    m = re.search(r'interest (\d+)', text)
    if m:
        target_interest = int(m.group(1))
        
    def add_interest(d):
        d["target_interest"] = target_interest
        return d
    
    # 8 Main Dataset Templates
    if 'trusted by thousands of customers worldwide' in text:
        return add_interest({"price_score": 0.0, "trust_score": 1.0, "urgency_score": 0.0, "emotion_score": 0.0})
    if 'join our community of happy buyers' in text:
        return add_interest({"price_score": 0.0, "trust_score": 0.8, "urgency_score": 0.0, "emotion_score": 0.8})
    if 'don\'t miss out, sale ends soon' in text:
        return add_interest({"price_score": 0.0, "trust_score": 0.0, "urgency_score": 1.0, "emotion_score": 0.0})
    if 'limited time offer on our newest products' in text:
        return add_interest({"price_score": 0.0, "trust_score": 0.0, "urgency_score": 1.0, "emotion_score": 0.0})
    if 'premium quality at an affordable price' in text:
        return add_interest({"price_score": 1.0, "trust_score": 0.5, "urgency_score": 0.0, "emotion_score": 0.0})
    if 'the perfect gift for your loved ones' in text:
        return add_interest({"price_score": 0.0, "trust_score": 0.0, "urgency_score": 0.0, "emotion_score": 1.0})
    if 'upgrade your lifestyle now' in text:
        return add_interest({"price_score": 0.0, "trust_score": 0.0, "urgency_score": 0.5, "emotion_score": 0.8})
    if 'discover the difference today' in text:
        return add_interest({"price_score": 0.0, "trust_score": 0.5, "urgency_score": 0.5, "emotion_score": 0.5})
    # --- Price Score (Deal Perceived Value) ---
    # High score if ad mentions discounts, free, savings, or deals.
    price_score = 0.5
    if re.search(r'\b(free|save|discount|% off|\$ off|deal|sale|clearance|cheap|affordable)\b', text):
        price_score += 0.25
        # Add more if there's a big percentage
        if re.search(r'(50%|60%|70%|80%|90%)', text):
            price_score += 0.15
        elif re.search(r'(20%|30%|40%)', text):
            price_score += 0.1
    # Check numeric price in text if present (e.g. $5)
    prices_found = re.findall(r'\$\d+', text)
    if prices_found:
        try:
            min_price = min([int(p.replace('$', '')) for p in prices_found])
            if min_price < 20:
                price_score += 0.1
        except:
            pass
            
    price_score = max(0.0, min(1.0, price_score))


    # --- Trust Score (Authority & Social Proof) ---
    trust_score = 0.5
    if re.search(r'\b(trusted|guarantee|warranty|secure|reviews|rated|experts|certified|proven|premium|quality|community)\b', text):
        trust_score += 0.2
        if 'money back' in text or 'guarantee' in text:
            trust_score += 0.1
        if 'stars' in text or 'rating' in text:
            trust_score += 0.1
    if re.search(r'\b(scam|fake|unreliable)\b', text):
        trust_score -= 0.3
        
    trust_score = max(0.0, min(1.0, trust_score))


    # --- Urgency Score (FOMO) ---
    urgency_score = 0.5
    if re.search(r'\b(urgent|now|limited time|hurry|today|last chance|ending soon|don\'t miss|expires|only \d+ left)\b', text):
        urgency_score += 0.25
        if 'today' in text or 'now' in text:
            urgency_score += 0.1
        if 'last chance' in text or 'ending soon' in text:
            urgency_score += 0.1
            
    urgency_score = max(0.0, min(1.0, urgency_score))

    # --- Emotion Score (Emotional Appeal) ---
    emotion_score = 0.5
    if re.search(r'\b(love|loved|gift|happy|family|friends|joy|beautiful|amazing|perfect|smile|heart|discover|lifestyle|buyers)\b', text):
        emotion_score += 0.3
        if 'loved ones' in text or 'gift' in text:
            emotion_score += 0.2
            
    emotion_score = max(0.0, min(1.0, emotion_score))

    return {
        "price_score": price_score,
        "trust_score": trust_score,
        "urgency_score": urgency_score,
        "emotion_score": emotion_score
    }

