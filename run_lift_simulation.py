"""Run lift simulation for GEO audit."""

from geo_audit_agent.graph_workflow import run_brand_audit_graph, _run_audit_direct


def run_lift_simulation(brand_name: str, category: str, city: str, business_data: dict = None):
    """
    Run lift simulation for a business using the industry-aware graph workflow.
    """
    print("RUN_LIFT_SIMULATION_ACTIVE_DIRECT_BYPASS")
    print(f"RUN_LIFT_INPUT_CATEGORY: {repr(category)}")

    if business_data is None:
        business_data = {}

    # Bypass LangGraph and run direct path
    results = _run_audit_direct(brand_name, category, city, business_data)

    # Normalize the result to match dashboard.py and unified output expectations
    normalized = {
        "brand": brand_name,
        "brand_name": brand_name,
        "category": category,
        "city": city,
        "template_used": results.get("template_used", "Generic"),
        "citation_found": results.get("citation_score", 1.0) > 0.5,
        "confidence_score": results.get("citation_score", 1.0),
        "sentiment": results.get("sentiment", "none"),
        "raw_response": business_data.get("raw_response", ""),
        "competitors": results.get("competitors", []),
        "strengths": results.get("strengths", []),
        "gaps": results.get("gaps", []),
        "remediation": results.get("planned_actions", results.get("remediation", [])),
        "mode": "simulated",
        "lift_metrics": results.get("lift_metrics", {}),
        "call_path": "run_lift_simulation_direct_bypass"
    }

    return normalized


if __name__ == '__main__':
    # Example: Capital Arena Fitness Club
    capital_arena_data = {
        'review_count': 231,
        'rating': 4.5,
        'services': [
            'online classes',
            'sauna',
            'swimming pool',
            'gym',
            'spa',
            'steam',
            'protein bar',
            'physiotherapy',
        ],
        'instagram_followers': 18300,
        'facebook_followers': 12200,
        'location_description': 'F-9 Park / Megazone, Islamabad',
        'is_central_location': True,
        'raw_response': (
            'Capital Arena Fitness Club stands out for its commitment to customer satisfaction. '
            '1. Capital Arena Fitness Club\n'
            '2. Local Favorite\n'
            '3. Established Brand'
        ),
        'has_schema': False,
        'has_trainer_info': False,
        'has_pricing': False,
        'has_schedule': False,
        'has_local_content': False,
    }

    results = run_lift_simulation(
        brand_name='Capital Arena Fitness Club',
        category='fitness gym',
        city='Islamabad',
        business_data=capital_arena_data
    )

    print('=== GEO Audit Results ===')
    print(f"Brand: {results['brand_name']}")
    print(f"Category: {results['category']}")
    print(f"City: {results['city']}")
    print(f"Template: {results['template_used']}")
    print()

    print('=== Sentiment ===')
    print(f"Sentiment: {results['sentiment']}")
    print()

    print('=== Competitors ===')
    if results['competitors']:
        for comp in results['competitors']:
            print(f"  - {comp}")
    else:
        print('  No competitors identified.')
    print()

    print('=== Strengths ===')
    for strength in results['strengths']:
        print(f"  [{strength['type']}] {strength['title']}: {strength['description']}")
    print()

    print('=== Gaps ===')
    for gap in results['gaps']:
        print(f"  [{gap['severity']}] {gap['title']}: {gap['description']}")
    print()

    print('=== Lift Metrics ===')
    lift = results['lift_metrics']
    print(f"Before Score: {lift['before_score']:.2f}")
    print(f"After Score: {lift['after_score']:.2f}")
    print(f"Absolute Lift: {lift['absolute_lift']:.2f}")
    print(f"Percentage Lift: {lift['percentage_lift']:.1f}%")
    print(f"Status: {lift['status']}")
    print(f"Message: {lift['message']}")
    print(f"Explanation: {lift['explanation']}")
    print()

    print('=== Remediation ===')
    if results['remediation']:
        for rem in results['remediation']:
            print(f"  [{rem['priority']}] {rem['title']}")
            print(f"    Reason: {rem['reason']}")
            print(f"    Action: {rem['action']}")
            print(f"    Effort: {rem['effort']} | Impact: {rem['impact']}")
            print()
    else:
        print('  No remediation results to display.')
