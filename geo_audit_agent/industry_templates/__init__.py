"""Industry-specific templates for GEO audit recommendations."""

from .fitness_gym import FitnessGymTemplate

TEMPLATES = {
    'fitness_gym': FitnessGymTemplate,
}

def get_template(category: str):
    """Get industry template based on category."""
    category_lower = category.lower()

    # Check for fitness/gym keywords
    fitness_keywords = ['fitness', 'gym', 'health club', 'training', 'personal training']
    if any(keyword in category_lower for keyword in fitness_keywords):
        return TEMPLATES['fitness_gym']()

    return None

__all__ = ['get_template', 'FitnessGymTemplate', 'TEMPLATES']
