import pytest
from geo_audit_agent.graph_workflow import run_brand_audit_graph


def test_dental_clinic_graph_workflow():
    """
    Regression test for the LangGraph/dashboard path for dental clinic.

    This test executes the same path used by Streamlit:
    query_llm → check_citation → gap_analyst → planner → remediation_handler → generate_report

    Input:
    brand_name = "Dental Solutions Islamabad"
    category = "dental clinic"
    city = "Islamabad, Pakistan"
    business_data with full context

    Assert:
    - template_used == "DentalClinicTemplate"
    - strengths length > 0
    - gaps length > 0
    - remediation length > 0
    - output does not contain "Template: Generic"
    - output does not contain "brand's schema.org"
    - output does not contain "No recent reviews found"
    """
    brand_name = "Dental Solutions Islamabad"
    category = "dental clinic"
    city = "Islamabad, Pakistan"
    business_data = {
        "business_context": (
            "Dental Solutions Islamabad is a dental clinic located at Clinic #201, 2nd Floor, Islamabad Diagnostic Center, F-8 Markaz, Islamabad. "
            "Website: dentalsolutionsisb.com. Phone numbers listed: +92 345 568 6306 and 051 2817045. "
            "The clinic claims 30+ years of dental experience, 7,950+ happy patients, 10,000+ successful treatments, and a 4.9/5 Google rating based on 63+ verified reviews. "
            "Services include general dentistry, cosmetic dentistry, dental implants, orthodontics, root canal treatment, teeth whitening, checkups, cleanings, preventive care, veneers, bonding, complete smile makeovers, braces, clear aligners, crowns, and bridges. "
            "The website mentions expert dentists, modern technology, affordable/transparent pricing, safe and hygienic care, 100% sterilization, patient safety, ISO certification, highest hygiene standards, and emergency call support. "
            "It has appointment booking, opening hours from Monday to Saturday 11:00 AM to 9:30 PM, Sunday closed, and testimonials mentioning quality dental care, clean and well-maintained clinic, sterilization, and professional dentists."
        ),
        "has_schema": False,
        "services": ["checkups", "cleanings"],
        "has_credentials": True,
        "has_emergency_info": True,
        "has_insurance_info": False,
        "has_hygiene_info": True,
        "has_faq": False,
        "has_local_comparison": False,
    }

    result = run_brand_audit_graph(brand_name, category, city, business_data)

    # Assert correct template
    assert result['template_used'] == 'DentalClinicTemplate', f"Expected DentalClinicTemplate, got {result.get('template_used')}"

    # Assert strengths
    assert len(result['strengths']) > 0, f"Expected strengths > 0, got {len(result.get('strengths', []))}"

    # Assert gaps
    assert len(result['gaps']) > 0, f"Expected gaps > 0, got {len(result.get('gaps', []))}"

    # Assert remediation (planned_actions)
    assert len(result.get('planned_actions', [])) > 0, f"Expected planned_actions > 0, got {len(result.get('planned_actions', []))}"

    # Assert no generic template
    assert result.get('template_used') != 'Generic', "Template should not be Generic"

    # Assert no generic gaps
    gap_titles = [g.get('title', '') for g in result.get('gaps', [])]
    gap_descriptions = ' '.join([g.get('description', '') for g in result.get('gaps', [])])

    assert "brand's schema.org" not in gap_titles
    assert "brand's schema.org" not in gap_descriptions
    assert "No recent reviews found" not in gap_titles
    assert "No recent reviews found" not in gap_descriptions

    # Assert dental-specific content is present
    all_text = str(result).lower()
    dental_terms = ['dentist', 'dental', 'braces', 'implants', 'whitening', 'root canal', 'medicalclinic']
    has_dental = any(term in all_text for term in dental_terms)
    assert has_dental, f"Expected dental-specific content, got: {all_text[:500]}"

    # Assert no ecommerce-only terms
    ecommerce_terms = ['product schema', 'offer schema', 'size guide', 'shipping', 'returns']
    for term in ecommerce_terms:
        assert term not in all_text, f"Found ecommerce term '{term}' in dental audit result"


def test_fitness_gym_graph_workflow():
    """Test that fitness gym graph workflow still works correctly."""
    brand_name = "Capital Arena Fitness Club"
    category = "fitness gym"
    city = "Islamabad"
    business_data = {
        "review_count": 231,
        "rating": 4.5,
        "services": ["online classes", "sauna", "swimming pool", "gym", "spa", "steam", "protein bar", "physiotherapy"],
        "instagram_followers": 18300,
        "facebook_followers": 12200,
        "location_description": "F-9 Park / Megazone, Islamabad",
        "is_central_location": True,
        "has_schema": False,
        "has_trainer_info": False,
        "has_pricing": False,
        "has_schedule": False,
        "has_local_content": False,
    }

    result = run_brand_audit_graph(brand_name, category, city, business_data)

    # Assert correct template
    assert result['template_used'] == 'FitnessGymTemplate'

    # Assert gaps and strengths exist
    assert len(result['gaps']) > 0
    assert len(result['strengths']) > 0

    # Assert fitness-specific content
    all_text = str(result).lower()
    fitness_terms = ['sportsactivitylocation', 'healthclub', 'trainer', 'swimming pool', 'sauna']
    has_fitness = any(term in all_text for term in fitness_terms)
    assert has_fitness, f"Expected fitness-specific content, got: {all_text[:500]}"

    # Assert no ecommerce-only terms in remediation
    planned_actions = result.get('planned_actions', [])
    for action in planned_actions:
        action_text = str(action).lower()
        assert 'product schema' not in action_text
        assert 'size guide' not in action_text
        assert 'shipping' not in action_text


def test_ecommerce_graph_workflow():
    """Test that ecommerce graph workflow still works correctly."""
    brand_name = "MEME Official Store"
    category = "online fashion store"
    city = "Pakistan"
    business_data = {
        "platform": "Shopify",
        "has_product_catalog": True,
        "has_return_policy": True,
        "return_policy_description": "14-day exchange window",
        "has_payment_options": True,
        "instagram_followers": 12000,
        "has_social_presence": True,
        "market": "Pakistan",
        "has_schema": False,
        "has_product_reviews": False,
        "has_shipping_info": False,
        "has_size_guide": False,
        "has_faq": False,
        "has_trust_badges": False,
        "has_comparison_content": False,
        "has_category_pages": False,
    }

    result = run_brand_audit_graph(brand_name, category, city, business_data)

    # Assert correct template
    assert result['template_used'] == 'EcommerceTemplate'

    # Assert gaps and strengths exist
    assert len(result['gaps']) > 0
    assert len(result['strengths']) > 0

    # Assert ecommerce-specific content
    all_text = str(result).lower()
    ecommerce_terms = ['product', 'offer', 'aggregate', 'shipping', 'returns']
    has_ecommerce = any(term in all_text for term in ecommerce_terms)
    assert has_ecommerce, f"Expected ecommerce-specific content, got: {all_text[:500]}"

    # Assert no fitness-only terms in remediation
    planned_actions = result.get('planned_actions', [])
    for action in planned_actions:
        action_text = str(action).lower()
        assert 'healthclub' not in action_text
        assert 'trainer credential' not in action_text
        assert 'class schedule' not in action_text
