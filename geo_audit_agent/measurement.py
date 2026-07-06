"""Lift measurement and visibility scoring for GEO audit."""

def measure_lift(before_score: float, after_score: float) -> dict:
    """
    Measure lift between before and after scores.

    Args:
        before_score: Baseline visibility score (0.0 to 1.0)
        after_score: Post-improvement visibility score (0.0 to 1.0)

    Returns:
        dict with lift metrics and status
    """
    absolute_lift = after_score - before_score

    # Avoid division by zero
    if before_score == 0:
        percentage_lift = 0.0 if after_score == 0 else 100.0
    else:
        percentage_lift = (absolute_lift / before_score) * 100

    # Determine lift status
    if absolute_lift < 0:
        status = "negative"
        message = "Visibility decreased"
        explanation = (
            "No lift detected. The brand already had strong baseline visibility, "
            "so improvements may produce marginal or negative simulated movement."
        )
    elif before_score >= 0.85:
        status = "baseline_strong"
        message = "Already strong visibility"
        explanation = (
            "The brand has strong baseline visibility (85%+). "
            "Recommend monitoring and optimization instead of aggressive improvement simulation."
        )
    elif absolute_lift < 0.05:
        status = "marginal"
        message = "Marginal lift detected"
        explanation = (
            "Small improvement detected. Consider more aggressive optimization strategies."
        )
    else:
        status = "positive"
        message = "Lift simulation completed"
        explanation = (
            f"Visibility improved by {percentage_lift:.1f}%. "
            "Recommendations are likely to produce measurable impact."
        )

    return {
        'before_score': before_score,
        'after_score': after_score,
        'absolute_lift': absolute_lift,
        'percentage_lift': percentage_lift,
        'status': status,
        'message': message,
        'explanation': explanation,
    }


def calculate_visibility_score(business_data: dict, gaps: list) -> float:
    """
    Calculate visibility score based on business data and gaps.

    Args:
        business_data: Business information and metrics
        gaps: List of identified gaps

    Returns:
        Visibility score between 0.0 and 1.0
    """
    score = 1.0

    # Penalize for gaps
    for gap in gaps:
        severity = gap.get('severity', 'medium')
        if severity == 'high':
            score -= 0.15
        elif severity == 'medium':
            score -= 0.10
        else:
            score -= 0.05

    # Bonus for strong signals
    review_count = business_data.get('review_count', 0)
    rating = business_data.get('rating', 0)

    if review_count >= 200 and rating >= 4.5:
        score += 0.10
    elif review_count >= 100 and rating >= 4.0:
        score += 0.05

    # Bonus for social presence
    instagram_followers = business_data.get('instagram_followers', 0)
    facebook_followers = business_data.get('facebook_followers', 0)

    if instagram_followers >= 15000 or facebook_followers >= 10000:
        score += 0.05

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, score))
