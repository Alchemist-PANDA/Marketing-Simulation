"""
Forensic Failure Analysis Module for Marketing Simulation.

Identifies why an ad creative failed to achieve optimal performance
and provides actionable feedback based on psychographic scores.
"""

from typing import Dict, List, Any

def analyze_failure(price_score: float, trust_score: float, urgency_score: float,
                    ctr: float, cvr: float) -> Dict[str, Any]:
    """
    Analyzes simulation metrics to identify top friction points.

    Args:
        price_score: Normalized price attractiveness (0-1)
        trust_score: Normalized brand trust (0-1)
        urgency_score: Normalized FOMO/Urgency (0-1)
        ctr: Simulated Click-Through Rate
        cvr: Simulated Conversion Rate

    Returns:
        Dictionary with top 3 failure reasons and original scores.
    """
    # Thresholds for "failure" detection
    LOW_SCORE_THRESHOLD = 0.4
    MED_SCORE_THRESHOLD = 0.6

    reasons = []

    # Check for Price failure
    if price_score < LOW_SCORE_THRESHOLD:
        reasons.append((price_score, "Price too high for perceived value"))
    elif price_score < MED_SCORE_THRESHOLD:
        reasons.append((price_score, "Weak pricing incentive"))

    # Check for Trust failure
    if trust_score < LOW_SCORE_THRESHOLD:
        reasons.append((trust_score, "Low trust signals - lacks social proof"))
    elif trust_score < MED_SCORE_THRESHOLD:
        reasons.append((trust_score, "Insufficient brand authority"))

    # Check for Urgency failure
    if urgency_score < LOW_SCORE_THRESHOLD:
        reasons.append((urgency_score, "Weak urgency - no incentive to act now"))
    elif urgency_score < MED_SCORE_THRESHOLD:
        reasons.append((urgency_score, "Low FOMO factor"))

    # Performance-based secondary reasons
    if ctr < 0.05 and len(reasons) < 3:
        reasons.append((0.0, "Creative lacks stopping power (Low CTR)"))

    if cvr < 0.02 and len(reasons) < 3:
        reasons.append((0.0, "Poor offer-to-audience fit (Low CVR)"))

    # Sort by score (ascending, lowest scores first) and take top 3
    # We use a secondary sort key to prioritize the pre-defined explanations
    reasons.sort(key=lambda x: x[0])
    top_reasons = [r[1] for r in reasons[:3]]

    # Fallback if everything looks "fine" but performance is still low
    if not top_reasons:
        top_reasons = ["Market saturation / High skepticism", "Generic creative messaging"]

    return {
        "failure_reasons": top_reasons,
        "scores": {
            "price": round(price_score, 2),
            "trust": round(trust_score, 2),
            "urgency": round(urgency_score, 2)
        },
        "performance": {
            "ctr": f"{ctr:.2%}",
            "cvr": f"{cvr:.2%}"
        }
    }

if __name__ == "__main__":
    # Test case: High price (low score), low trust, high urgency
    test_result = analyze_failure(0.2, 0.3, 0.9, 0.02, 0.01)
    print("Failure Analysis Output:")
    import json
    print(json.dumps(test_result, indent=2))
