"""Industry-specific templates for GEO audit recommendations."""

from .fitness_gym import FitnessGymTemplate
from .ecommerce import EcommerceTemplate
from .dental_clinic import DentalClinicTemplate

TEMPLATES = {
    'fitness_gym': FitnessGymTemplate,
    'ecommerce': EcommerceTemplate,
    'dental_clinic': DentalClinicTemplate,
}

def get_template(category: str):
    """Get industry template based on category."""
    if not category:
        return None

    category_lower = category.lower().strip()

    # Check for ecommerce keywords
    ecommerce_keywords = [
        'ecommerce', 'e-commerce', 'online store', 'online shop', 'fashion store',
        'clothing store', 'shopify', 'retail', 'marketplace', 'skincare store',
        'electronics store', 'furniture store'
    ]
    if any(keyword in category_lower for keyword in ecommerce_keywords):
        return TEMPLATES['ecommerce']()

    # Check for fitness/gym keywords
    fitness_keywords = ['fitness', 'gym', 'health club', 'training', 'personal training']
    if any(keyword in category_lower for keyword in fitness_keywords):
        return TEMPLATES['fitness_gym']()

    # Check for dental keywords
    dental_keywords = [
        'dental clinic', 'dentist', 'dental care', 'orthodontist', 'braces',
        'dental implants', 'cosmetic dentistry', 'emergency dentist',
        'teeth whitening', 'root canal', 'pediatric dentist', 'dental'
    ]
    if any(keyword in category_lower for keyword in dental_keywords):
        return TEMPLATES['dental_clinic']()

    return None

__all__ = ['get_template', 'FitnessGymTemplate', 'EcommerceTemplate', 'DentalClinicTemplate', 'TEMPLATES']
