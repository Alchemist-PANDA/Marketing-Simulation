"""
Feature extraction and scoring module for marketing simulation.
Converts raw ad attributes and text content into normalized scores (0-1).

Two scoring tiers:
1. Text-aware keyword scoring (extract_text_scores) - analyzes ad copy
2. Attribute-based scoring (extract_scores) - uses numeric fields as fallback
"""

import re
from typing import Dict, Any


_PRICE_POSITIVE = [
    "save", "discount", "off", "sale", "deal", "cheap", "affordable",
    "free", "clearance", "bargain", "low price", "half price", "reduced",
    "buy 1 get 1", "bogo", "coupon", "promo", "value", "budget",
    "50%", "70%", "80%", "90%", "percent off", "save money",
    "shipping", "free shipping", "first order",
]
_PRICE_NEGATIVE = [
    "premium", "luxury", "exclusive", "expensive", "elite", "high-end",
    "bespoke", "artisan", "handcrafted", "collector", "listings",
]

_TRUST_POSITIVE = [
    "trusted", "review", "guarantee", "certified", "verified",
    "authentic", "award", "proven", "millions", "rated", "recommended",
    "secure", "reliable", "professional", "quality", "100%", "natural",
    "organic", "safe", "tested",
]
_TRUST_NEGATIVE = [
    "unknown", "experimental", "beta", "untested", "secret",
]

_URGENCY_POSITIVE = [
    "limited time", "today only", "last chance", "hurry", "now",
    "quick", "ends tonight", "flash sale", "only", "left",
    "don't miss", "act now", "deadline", "expires", "final",
    "clearance", "closing", "running out", "before it's gone",
    "early bird", "book now", "starting now", "tonight",
    "today", "switch", "everything must go", "must go",
]

# Action verbs that signal direct-response intent (boosts engagement)
_ACTION_VERBS = [
    "learn", "get", "try", "book", "download", "switch", "upgrade",
    "discover", "join", "start", "buy", "shop", "order", "sign up",
    "subscribe", "register", "claim", "grab", "experience",
]


def _count_matches(text_lower: str, keywords: list) -> int:
    return sum(1 for kw in keywords if kw in text_lower)


def extract_text_scores(text: str) -> Dict[str, float]:
    """
    Extract price/trust/urgency scores from ad text using keyword analysis.

    Returns scores in [0, 1] based on the presence and density of
    persuasion-related keywords in the text.
    """
    text_lower = text.lower()

    price_pos = _count_matches(text_lower, _PRICE_POSITIVE)
    price_neg = _count_matches(text_lower, _PRICE_NEGATIVE)

    if price_pos + price_neg == 0:
        price_score = 0.5
    else:
        price_score = 0.5 + 0.15 * price_pos - 0.15 * price_neg
        price_score = max(0.1, min(0.95, price_score))

    trust_pos = _count_matches(text_lower, _TRUST_POSITIVE)
    trust_neg = _count_matches(text_lower, _TRUST_NEGATIVE)

    if trust_pos + trust_neg == 0:
        trust_score = 0.45
    else:
        # Diminishing returns: first keyword +0.15, subsequent +0.05 each
        trust_boost = min(trust_pos, 1) * 0.15 + max(trust_pos - 1, 0) * 0.05
        trust_score = 0.45 + trust_boost - 0.10 * trust_neg
        trust_score = max(0.1, min(0.95, trust_score))

    urgency_pos = _count_matches(text_lower, _URGENCY_POSITIVE)

    if urgency_pos == 0:
        urgency_score = 0.3
    else:
        urgency_score = 0.3 + 0.20 * urgency_pos
        urgency_score = max(0.1, min(0.95, urgency_score))

    # Boost for explicit percentage mentions (strong price signal)
    pct_matches = re.findall(r'(\d+)%', text)
    for pct_str in pct_matches:
        pct = int(pct_str)
        if pct >= 20:
            price_score = min(0.95, price_score + 0.10)
            urgency_score = min(0.95, urgency_score + 0.05)

    # Boost for exclamation marks (emotional intensity)
    excl_count = text.count('!')
    if excl_count >= 2:
        urgency_score = min(0.95, urgency_score + 0.05)

    # Action verb boost: direct-response copy generally outperforms passive
    action_count = _count_matches(text_lower, _ACTION_VERBS)
    if action_count > 0:
        urgency_score = min(0.95, urgency_score + 0.05 * min(action_count, 2))
        price_score = min(0.95, price_score + 0.03 * min(action_count, 2))

    return {
        "price_score": round(price_score, 4),
        "trust_score": round(trust_score, 4),
        "urgency_score": round(urgency_score, 4),
    }


def extract_scores(ad_data: Dict[str, Any],
                   price_scale: float = 50.0) -> Dict[str, float]:
    """
    Extract normalized scores from raw ad data.

    If the ad_data contains a 'text' field, text-based scoring is attempted
    first. Falls back to attribute-based scoring if text produces no signal
    or is absent.
    """
    text = ad_data.get('text', '')
    if text and isinstance(text, str) and len(text.strip()) > 5:
        text_scores = extract_text_scores(text)
        has_signal = (
            text_scores['price_score'] != 0.5
            or text_scores['trust_score'] != 0.45
            or text_scores['urgency_score'] != 0.3
        )
        if has_signal:
            return text_scores

    # Attribute-based fallback
    price = ad_data.get('price', 10.0)
    price_score = 1.0 / (1.0 + price / price_scale)
    price_score = max(0.0, min(1.0, price_score))

    social_proof = ad_data.get('social_proof', 2.5)
    trust_base = social_proof / 5.0
    trust_score = 0.2 + 0.8 * trust_base

    category = ad_data.get('category', '')
    if category == 'luxury':
        trust_score = min(1.0, trust_score * 1.1)

    trust_score = max(0.0, min(1.0, trust_score))

    urgency_raw = ad_data.get('urgency', 2.5)
    urgency_score = urgency_raw / 5.0
    urgency_score = max(0.0, min(1.0, urgency_score))

    return {
        "price_score": price_score,
        "trust_score": trust_score,
        "urgency_score": urgency_score
    }
