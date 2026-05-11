"""Industry-specific templates for GEO audit recommendations."""

from .fitness_gym import FitnessGymTemplate
from .ecommerce import EcommerceTemplate

TEMPLATES = {
    'fitness_gym': FitnessGymTemplate,
    'ecommerce': EcommerceTemplate,
}

def get_template(category: str):
    """Get industry template based on category."""
    category_lower = category.lower()

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

    return None

__all__ = ['get_template', 'FitnessGymTemplate', 'EcommerceTemplate', 'TEMPLATES']
