"""Remediation generation for GEO audit gaps."""

from typing import List, Dict
from .industry_templates import get_template


def generate_remediation(gaps: List[Dict], category: str, city: str, brand_name: str) -> List[Dict]:
    """
    Generate remediation recommendations for identified gaps.

    Args:
        gaps: List of identified gaps from audit
        category: Business category
        city: City location
        brand_name: Business name

    Returns:
        List of remediation recommendations
    """
    if not gaps:
        return []

    remediation = []
    template = get_template(category)
    is_ecommerce = template and template.__class__.__name__ == 'EcommerceTemplate'

    for gap in gaps:
        gap_type = gap.get('type', 'generic')
        severity = gap.get('severity', 'medium')
        title = gap.get('title', 'Unknown gap')

        # Determine priority
        priority = 'high' if severity == 'high' else 'medium' if severity == 'medium' else 'low'

        # Generate remediation based on gap type
        if gap_type == 'schema':
            if is_ecommerce:
                remediation.append({
                    'priority': priority,
                    'type': 'schema',
                    'title': 'Add structured data markup',
                    'reason': title,
                    'why_this_works': 'Structured data helps search engines understand your products, pricing, and reviews, improving visibility in shopping results.',
                    'action': 'Implement Product, Offer, AggregateRating, and Review schema on your website.',
                    'effort': 'medium',
                    'impact': 'high',
                    'quick_win': True,
                })
            else:
                remediation.append({
                    'priority': priority,
                    'type': 'schema',
                    'title': 'Add structured data markup',
                    'reason': title,
                    'why_this_works': 'Structured data helps search engines understand your business type, services, and location, improving visibility in local search results.',
                    'action': 'Implement LocalBusiness, SportsActivityLocation, and HealthClub schema on your website.',
                    'effort': 'medium',
                    'impact': 'high',
                    'quick_win': True,
                })

        elif gap_type == 'content':
            if is_ecommerce:
                if 'shipping' in title.lower() or 'return' in title.lower():
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Publish shipping and returns information',
                        'reason': title,
                        'why_this_works': 'Clear shipping and return details reduce cart abandonment.',
                        'action': 'Add shipping and return/exchange policy clearly on product pages.',
                        'effort': 'low',
                        'impact': 'high',
                        'quick_win': True,
                    })
                elif 'size' in title.lower() or 'fit' in title.lower():
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Add size guide and fit details',
                        'reason': title,
                        'why_this_works': 'Fit guidance reduces returns and increases conversion rates.',
                        'action': 'Add size guide and fit details to product pages.',
                        'effort': 'medium',
                        'impact': 'medium',
                        'quick_win': False,
                    })
                elif 'comparison' in title.lower() or 'category' in title.lower():
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Create category landing pages',
                        'reason': title,
                        'why_this_works': 'Target high-intent product category keywords.',
                        'action': 'Create high-intent category pages and comparison content.',
                        'effort': 'high',
                        'impact': 'high',
                        'quick_win': False,
                    })
                else:
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Add FAQ sections',
                        'reason': title,
                        'why_this_works': 'FAQs address customer objections directly.',
                        'action': 'Add FAQ sections to product and category pages.',
                        'effort': 'low',
                        'impact': 'medium',
                        'quick_win': True,
                    })
            else:
                if 'service' in title.lower():
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Create dedicated service pages',
                        'reason': title,
                        'why_this_works': 'Individual service pages target specific search queries and help Google understand your full service offering.',
                        'action': f'Create pages for: personal training, swimming pool, sauna, weight loss programs. Include pricing, benefits, and booking CTAs.',
                        'effort': 'high',
                        'impact': 'high',
                        'quick_win': False,
                    })
                elif 'trainer' in title.lower():
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Add trainer credential sections',
                        'reason': title,
                        'why_this_works': 'Trainer credentials build trust and target "personal trainer near me" queries.',
                        'action': 'Add trainer bios with certifications, specializations, and photos to your website.',
                        'effort': 'low',
                        'impact': 'medium',
                        'quick_win': True,
                    })
                elif 'pricing' in title.lower():
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Publish membership pricing',
                        'reason': title,
                        'why_this_works': 'Transparent pricing reduces friction and targets "gym membership cost" queries.',
                        'action': 'Create a pricing page with membership tiers, benefits, and sign-up options.',
                        'effort': 'low',
                        'impact': 'medium',
                        'quick_win': True,
                    })
                elif 'schedule' in title.lower():
                    remediation.append({
                        'priority': priority,
                        'type': 'content',
                        'title': 'Publish class schedule',
                        'reason': title,
                        'why_this_works': 'Class schedules target "gym classes near me" and help users plan their visits.',
                        'action': 'Add a class timetable with instructor names, class types, and booking links.',
                        'effort': 'low',
                        'impact': 'medium',
                        'quick_win': True,
                    })

        elif gap_type == 'local_seo':
            if not is_ecommerce:
                remediation.append({
                    'priority': priority,
                    'type': 'local_seo',
                    'title': f'Create local intent content for {city}',
                    'reason': title,
                    'why_this_works': f'Local intent content targets "best gym in {city}" queries and establishes local authority.',
                    'action': f'Create pages for: "best gym with pool in {city}", "best premium gym in {city}", "best gym for personal training in {city}". Include facility photos, member testimonials, and location details.',
                    'effort': 'medium',
                    'impact': 'high',
                    'quick_win': False,
                })

        elif gap_type == 'reviews':
            if is_ecommerce:
                remediation.append({
                    'priority': priority,
                    'type': 'reviews',
                    'title': 'Collect product-specific reviews',
                    'reason': title,
                    'why_this_works': 'Product reviews build trust and provide user-generated content for product pages.',
                    'action': 'Collect product-specific reviews mentioning quality, fit, delivery, packaging.',
                    'effort': 'medium',
                    'impact': 'high',
                    'quick_win': False,
                })
            else:
                remediation.append({
                    'priority': priority,
                    'type': 'reviews',
                    'title': 'Collect targeted reviews',
                    'reason': title,
                    'why_this_works': 'Reviews with specific keywords (trainers, cleanliness, equipment) improve relevance for those search queries.',
                    'action': 'Request reviews from satisfied members. Ask them to mention specific aspects: trainers, cleanliness, equipment, results, sauna, pool.',
                    'effort': 'low',
                    'impact': 'high',
                    'quick_win': True,
                })

        elif gap_type == 'trust':
            if is_ecommerce:
                remediation.append({
                    'priority': priority,
                    'type': 'trust',
                    'title': 'Improve trust signals',
                    'reason': title,
                    'why_this_works': 'Trust badges reassure buyers during checkout.',
                    'action': 'Add trust badges and secure payment indicators.',
                    'effort': 'low',
                    'impact': 'high',
                    'quick_win': True,
                })

    # Add Google Business Profile optimization if template exists and not ecommerce
    if template and remediation and not is_ecommerce:
        remediation.append({
            'priority': 'high',
            'type': 'local_seo',
            'title': 'Optimize Google Business Profile',
            'reason': 'Improve local search visibility',
            'why_this_works': 'Google Business Profile is the primary source for local search results and map pack rankings.',
            'action': 'Add facility photos, post class updates weekly, update service list, respond to all reviews, add Q&A section.',
            'effort': 'medium',
            'impact': 'high',
            'quick_win': True,
        })

    return remediation
