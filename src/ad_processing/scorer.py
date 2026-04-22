"""
Feature extraction and scoring module for marketing simulation.
Converts raw ad attributes into normalized scores (0-1).
"""

from typing import Dict, Any

def extract_scores(ad_data: Dict[str, Any],
                   price_scale: float = 50.0) -> Dict[str, float]:
    """
    Extract normalized scores from raw ad data.

    Args:
        ad_data: Dictionary with keys:
            - price (float): monetary value
            - category (str): product category (e.g., 'luxury')
            - social_proof (float): 0-5 rating
            - urgency (float): 0-5 urgency level
        price_scale: Sigmoid scaling factor for price_score (default 50)

    Returns:
        Dictionary with price_score, trust_score, and urgency_score.
    """
    # 1. Price score: inversely related to price using logistic decay
    price = ad_data.get('price', 10.0)
    price_score = 1.0 / (1.0 + price / price_scale)
    price_score = max(0.0, min(1.0, price_score))

    # 2. Trust score: from social_proof (0-5)
    social_proof = ad_data.get('social_proof', 2.5) # Default to mid-point
    trust_base = social_proof / 5.0
    trust_score = 0.2 + 0.8 * trust_base

    category = ad_data.get('category', '')
    if category == 'luxury':
        trust_score = min(1.0, trust_score * 1.1)

    trust_score = max(0.0, min(1.0, trust_score))

    # 3. Urgency score: linear scaling from 0-5 to 0-1
    urgency_raw = ad_data.get('urgency', 2.5) # Default to mid-point
    urgency_score = urgency_raw / 5.0
    urgency_score = max(0.0, min(1.0, urgency_score))

    return {
        "price_score": price_score,
        "trust_score": trust_score,
        "urgency_score": urgency_score
    }
