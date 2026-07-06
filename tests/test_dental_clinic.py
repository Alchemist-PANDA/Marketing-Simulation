import pytest
from geo_audit_agent.industry_templates import get_template
from geo_audit_agent.industry_templates.dental_clinic import DentalClinicTemplate
from geo_audit_agent.industry_templates.fitness_gym import FitnessGymTemplate
from geo_audit_agent.industry_templates.ecommerce import EcommerceTemplate

def test_dental_category_detection():
    """Test that dental categories are correctly detected."""
    dental_categories = [
        "Dental Clinic",
        "Emergency Dentist",
        "Pediatric Dentist",
        "Orthodontist London",
        "Cosmetic Dentistry Clinic"
    ]

    for category in dental_categories:
        template = get_template(category)
        assert isinstance(template, DentalClinicTemplate), f"Failed to detect {category} as dental"

def test_dental_template_logic():
    """Test dental template specific logic for strengths and gaps."""
    template = DentalClinicTemplate()

    business_data = {
        'name': 'Bright Smile Dental',
        'category': 'Dental Clinic',
        'city': 'New York',
        'review_count': 60,
        'rating': 4.7,
        'services': ['teeth whitening', 'braces', 'implants', 'emergency dentistry'],
        'has_schema': False,
        'has_credentials': True,
        'has_emergency_info': True,
        'has_insurance_info': False,
        'has_hygiene_info': False,
        'has_faq': False,
        'has_local_comparison': False,
        'hygiene_review_mentions': 12,
        'is_central_location': True
    }

    gaps = template.get_gaps(business_data)
    strengths = template.get_strengths(business_data)

    # Verify gaps
    gap_titles = [g['title'] for g in gaps]
    assert 'Missing structured data' in gap_titles
    assert 'Missing insurance/payment info' in gap_titles
    assert 'Missing hygiene/safety information' in gap_titles
    assert 'Missing local comparison content' in gap_titles

    # Verify dental specific schema in remediation (checking playbook since get_gaps returns descriptions)
    assert 'Add Dentist schema' in template.remediation_playbook['schema']['actions']
    assert 'Add MedicalClinic schema' in template.remediation_playbook['schema']['actions']

    # Verify strengths
    strength_titles = [s['title'] for s in strengths]
    assert 'Strong review base' in strength_titles
    assert 'Specialized treatment depth' in strength_titles
    assert 'Documented dentist credentials' in strength_titles
    assert 'Emergency availability' in strength_titles
    assert 'Hygiene/Cleanliness reputation' in strength_titles

def test_dental_vs_fitness_logic():
    """Test that dental logic does not output fitness recommendations."""
    template = DentalClinicTemplate()

    # Check that dental recommendations don't contain fitness terms
    remediation_actions = []
    for category in template.remediation_playbook.values():
        remediation_actions.extend(category['actions'])

    fitness_terms = ['HealthClub', 'SportsActivityLocation', 'trainer credentials', 'class schedule']
    for action in remediation_actions:
        for term in fitness_terms:
            assert term.lower() not in action.lower(), f"Dental action '{action}' contains fitness term '{term}'"

def test_dental_vs_ecommerce_logic():
    """Test that dental logic does not output e-commerce recommendations."""
    template = DentalClinicTemplate()

    # Check that dental recommendations don't contain ecommerce terms
    remediation_actions = []
    for category in template.remediation_playbook.values():
        remediation_actions.extend(category['actions'])

    ecommerce_terms = ['Product schema', 'Offer schema', 'size guide']
    for action in remediation_actions:
        for term in ecommerce_terms:
            assert term.lower() not in action.lower(), f"Dental action '{action}' contains ecommerce term '{term}'"

def test_existing_fitness_gym_detection():
    """Ensure existing fitness detection still works."""
    fitness_categories = ["Gym", "Fitness Club", "Personal Training Studio"]
    for category in fitness_categories:
        template = get_template(category)
        assert isinstance(template, FitnessGymTemplate)

def test_existing_ecommerce_detection():
    """Ensure existing ecommerce detection still works."""
    ecommerce_categories = ["Online Store", "Shopify Store", "Clothing Store"]
    for category in ecommerce_categories:
        template = get_template(category)
        assert isinstance(template, EcommerceTemplate)
