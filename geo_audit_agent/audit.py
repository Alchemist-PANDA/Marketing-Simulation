"""GEO audit logic with industry-specific templates."""

import re
from typing import Optional
from .industry_templates import get_template


def detect_sentiment(raw_response: str, brand_name: str) -> str:
    """
    Detect sentiment based on brand mention and nearby positive terms.

    Args:
        raw_response: Raw text response to analyze
        brand_name: Brand name to look for

    Returns:
        'positive', 'neutral', or 'none'
    """
    if not brand_name or not raw_response:
        return 'none'

    # Check if brand is mentioned
    brand_pattern = re.compile(re.escape(brand_name), re.IGNORECASE)
    brand_match = brand_pattern.search(raw_response)

    if not brand_match:
        return 'none'

    # Brand is mentioned - check for positive terms nearby
    positive_terms = [
        'best', 'top', 'excellent', 'quality', 'stands out', 'trusted',
        'popular', 'premium', 'well-maintained', 'supportive', 'clean',
        'recommended', 'commitment', 'customer satisfaction', 'outstanding',
        'exceptional', 'great', 'amazing', 'wonderful', 'fantastic',
        'highly rated', 'well-reviewed', 'professional', 'friendly',
    ]

    # Get text around brand mention (100 chars before and after)
    start = max(0, brand_match.start() - 100)
    end = min(len(raw_response), brand_match.end() + 100)
    context = raw_response[start:end].lower()

    # Check for positive terms in context
    for term in positive_terms:
        if term in context:
            return 'positive'

    # Brand mentioned but no clear sentiment
    return 'neutral'


def extract_competitors(raw_response: str, brand_name: str) -> list:
    """
    Extract competitors from raw response, excluding target brand and generic placeholders.

    Args:
        raw_response: Raw text response containing competitor list
        brand_name: Target brand name to exclude

    Returns:
        List of competitor names
    """
    if not raw_response:
        return []

    # Generic placeholders to exclude
    generic_placeholders = [
        'local favorite',
        'established brand',
        'premium choice',
        'top provider',
        'popular option',
        'leading brand',
        'market leader',
        'industry leader',
    ]

    competitors = []

    # Extract numbered list items (e.g., "1. Competitor Name")
    numbered_pattern = re.compile(r'^\s*\d+\.\s*(.+)$', re.MULTILINE)
    matches = numbered_pattern.findall(raw_response)

    for match in matches:
        competitor = match.strip()

        # Skip if it's the target brand
        if brand_name and brand_name.lower() in competitor.lower():
            continue

        # Skip generic placeholders
        if competitor.lower() in generic_placeholders:
            continue

        # Skip if too short or too long
        if len(competitor) < 3 or len(competitor) > 100:
            continue

        competitors.append(competitor)

    return competitors


def run_audit(brand_name: str, category: str, city: str, business_data: Optional[dict] = None) -> dict:
    """
    Run GEO audit for a business.

    Args:
        brand_name: Business name
        category: Business category (e.g., 'fitness gym')
        city: City location
        business_data: Optional business data (reviews, rating, services, etc.)

    Returns:
        Audit results with gaps, strengths, sentiment, competitors
    """
    if business_data is None:
        business_data = {}

    # Add city to business data
    business_data['city'] = city

    # Get industry template
    template = get_template(category)

    gaps = []
    strengths = []

    if template:
        # Use industry-specific template
        gaps = template.get_gaps(business_data)
        strengths = template.get_strengths(business_data)
    else:
        # Generic gaps if no template
        if not business_data.get('has_schema'):
            gaps.append({
                'type': 'schema',
                'severity': 'high',
                'title': 'Missing structured data',
                'description': 'No LocalBusiness schema detected',
            })

        review_count = business_data.get('review_count', 0)
        if review_count == 0:
            gaps.append({
                'type': 'reviews',
                'severity': 'high',
                'title': 'No recent reviews found',
                'description': 'No reviews detected',
            })

    # Detect sentiment (simulated for now)
    raw_response = business_data.get('raw_response', '')
    sentiment = detect_sentiment(raw_response, brand_name)

    # Extract competitors (simulated for now)
    competitors = extract_competitors(raw_response, brand_name)

    return {
        'brand_name': brand_name,
        'category': category,
        'city': city,
        'gaps': gaps,
        'strengths': strengths,
        'sentiment': sentiment,
        'competitors': competitors,
        'template_used': template.__class__.__name__ if template else None,
    }
