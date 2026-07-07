"""Industry-specific templates for GEO audit recommendations."""

from .fitness_gym import FitnessGymTemplate
from .ecommerce import EcommerceTemplate
from .dental_clinic import DentalClinicTemplate

TEMPLATES = {
    'fitness_gym': FitnessGymTemplate,
    'ecommerce': EcommerceTemplate,
    'dental_clinic': DentalClinicTemplate,
}

def get_template(category):
    """Get industry template based on category."""
    if not category:
        return None

    category_norm = str(category).lower().strip()

    templates = [
        FitnessGymTemplate(),
        EcommerceTemplate(),
        DentalClinicTemplate(),
    ]

    for template in templates:
        for trigger in template.category_triggers:
            trigger_norm = str(trigger).lower().strip()
            if trigger_norm in category_norm or category_norm in trigger_norm:
                return template

    return None

__all__ = ['get_template', 'FitnessGymTemplate', 'EcommerceTemplate', 'DentalClinicTemplate', 'TEMPLATES']
