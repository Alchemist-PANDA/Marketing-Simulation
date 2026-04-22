"""
Emotional response engine based on Big Five traits.
Zero API cost.
"""

from src.agents.base_agent import Personality

class EmotionEngine:
    """Predicts emotional valence of an interaction"""

    def __init__(self):
        pass

    def predict(self, personality: Personality, ad: 'Ad') -> float:
        """
        Calculates emotional modifier for ad engagement.
        Returns a float between -1.0 (very negative) and 1.0 (very positive).
        """
        # Basic heuristic model
        base = 0.0

        # Extroverts react more positively to social ads
        if ad.channel in ['facebook', 'tiktok', 'instagram']:
            base += personality.extraversion * 0.3

        # Conscientious people prefer structured, informative ads (like search)
        if ad.channel in ['google', 'search', 'email']:
            base += personality.conscientiousness * 0.4

        # Neuroticism makes agents more skeptical of novel or flashy ads
        if ad.creative_type in ['video', 'flashy']:
            base -= personality.neuroticism * 0.5

        # Openness leads to positive reactions to novel creative types
        if ad.creative_type in ['video', 'interactive']:
            base += personality.openness * 0.4

        # Clamp to -1, 1
        return max(min(base, 1.0), -1.0)
