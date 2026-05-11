import pytest
from geo_audit_agent.audit import run_audit
from geo_audit_agent.remediation import generate_remediation
from geo_audit_agent.industry_templates import get_template

def test_dental_clinic_production_regression():
    """Bug 1: Verify Dental Clinic uses DentalClinicTemplate and populates correctly."""
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
        "services": ["checkups", "cleanings"], # Missing specialized ones from template
        "has_credentials": True,
        "has_emergency_info": True,
        "has_insurance_info": False,
        "has_hygiene_info": True,
        "has_faq": False,
        "has_local_comparison": False,
    }

    results = run_audit(brand_name, category, city, business_data)

    # Assert correct template
    assert results['template_used'] == 'DentalClinicTemplate'
    assert len(results['strengths']) > 0
    assert len(results['gaps']) > 0

    # Generate remediation
    remediation = generate_remediation(results['gaps'], category, city, brand_name)
    assert len(remediation) > 0

    all_remediation_actions = ' '.join([str(r.get('action', '')).lower() for r in remediation])

    # Check for dental specific schema/actions
    assert 'dentist' in all_remediation_actions or 'medicalclinic' in all_remediation_actions
    assert 'braces' in all_remediation_actions or 'implants' in all_remediation_actions
    assert 'hygiene' in all_remediation_actions or 'sterilization' in all_remediation_actions or 'safety' in all_remediation_actions

    # Should NOT contain generic or ecommerce output
    assert "brand's schema.org" not in all_remediation_actions
    assert "no recent reviews found" not in [g['title'].lower() for g in results['gaps']]

    ecommerce_terms = ['product', 'offer', 'size guide', 'shipping', 'returns']
    for term in ecommerce_terms:
        # Some overlap is okay if it's natural (like 'product' in a sentence),
        # but specific ecomm recommendations shouldn't be there.
        # Checking schema specific strings
        assert 'product schema' not in all_remediation_actions
        assert 'offer schema' not in all_remediation_actions
        assert 'size guide' not in all_remediation_actions

def test_fitness_remediation_isolation():
    """Bug 2: Verify Fitness Gym remediation does not contain ecommerce actions."""
    category = "fitness gym"
    city = "Islamabad"
    gaps = [
        {'type': 'schema', 'severity': 'high', 'title': 'Missing schema'},
        {'type': 'content', 'severity': 'medium', 'title': 'Missing service pages'},
        {'type': 'content', 'severity': 'medium', 'title': 'Missing trainer credentials'},
    ]

    remediation = generate_remediation(gaps, category, city, "Capital Arena")

    all_actions = ' '.join([r['action'].lower() for r in remediation])

    # Check for fitness specific actions
    assert 'sportsactivitylocation' in all_actions or 'healthclub' in all_actions
    assert 'trainer' in all_actions
    assert 'service pages' in all_actions

    # Check for EXCLUSION of ecommerce actions
    ecommerce_actions = [
        'product, offer',
        'shipping',
        'return/exchange',
        'size guide',
        'trust badges',
        'secure payment'
    ]
    for action in ecommerce_actions:
        assert action not in all_actions

def test_ecommerce_remediation_isolation():
    """Verify Ecommerce remediation still works correctly."""
    category = "online fashion store"
    city = "Pakistan"
    gaps = [
        {'type': 'schema', 'severity': 'high', 'title': 'Missing schema'},
        {'type': 'content', 'severity': 'medium', 'title': 'Missing size guide'},
    ]

    remediation = generate_remediation(gaps, category, city, "MEME")

    all_actions = ' '.join([r['action'].lower() for r in remediation])

    # Check for ecommerce specific actions
    assert 'product' in all_actions
    assert 'offer' in all_actions
    assert 'size guide' in all_actions

    # Check for EXCLUSION of fitness/dental actions
    assert 'healthclub' not in all_actions
    assert 'trainer' not in all_actions
    assert 'dentist' not in all_actions

def test_trigger_regression():
    """Confirm all triggers still work as expected."""
    assert get_template("dental clinic").__class__.__name__ == "DentalClinicTemplate"
    assert get_template("dentist").__class__.__name__ == "DentalClinicTemplate"
    assert get_template("online fashion store").__class__.__name__ == "EcommerceTemplate"
    assert get_template("fitness gym").__class__.__name__ == "FitnessGymTemplate"
