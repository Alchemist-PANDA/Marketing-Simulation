"""
Decision Engine using Big Five traits for behavioral modeling.
Zero API cost. Pure mathematical utility functions.
"""

from typing import Dict, Any, List, Optional
import math
from .agent import Agent

class DecisionEngine:
    """
    Mathematical model of consumer choice.
    Uses psychographic weights to drive behavior.
    """

    def decide_action(
        self,
        agent: Any,
        context: Dict[str, Any],
        options: List[str]
    ) -> str:
        """
        Calculates utility for each option based on agent personality.
        """
        if not options:
            return "idle"

        utilities = {}
        for option in options:
            utilities[option] = self._calculate_utility(agent, option, context)

        # Softmax selection or simple max
        return max(utilities, key=utilities.get)

    def calculate_response_probability(self, agent: Any, campaign: Dict[str, Any]) -> float:
        """
        Legacy/Alias for compatibility with older tests.
        Calculates a response probability (0-1).
        """
        # If agent is a dict (legacy test style), convert to object-like or use directly
        if isinstance(agent, dict):
            # Extract basic traits
            ps = agent.get('price_sensitivity', 0.5)
            ds = agent.get('digital_savviness', 0.5)
            pc = agent.get('preferred_channel', '')
        else:
            ps = getattr(agent.personality, 'price_sensitivity', 0.5)
            ds = getattr(agent.personality, 'openness', 0.5) # Using openness as proxy for digital_savviness
            pc = '' # Placeholder

        modifier = campaign.get('effectiveness_modifier', 1.0)
        target_trait_val = ds if campaign.get('trait_target') == 'digital_savviness' else (1-ps)

        prob = target_trait_val * modifier
        if pc == campaign.get('channel'):
            prob *= 1.2

        return max(0.0, min(1.0, prob))

    def _calculate_utility(self, agent: Agent, option: str, context: Dict[str, Any]) -> float:
        """Utility function driven by Big Five traits"""
        utility = 0.0

        if option == "buy":
            # Price vs sensitivity
            price = context.get("price", 10.0)
            if agent.state.money < price:
                return -100.0 # Can't afford

            price_pain = price * agent.personality.price_sensitivity
            quality_gain = 20.0 * (1 - agent.personality.ad_skepticism)

            # Conscientiousness = careful spending
            # Extraversion = social signalling value
            social_value = 5.0 * agent.personality.extraversion

            utility = quality_gain - price_pain + social_value

        elif option == "share":
            # Extraversion and Agreeableness drive sharing
            utility = (agent.personality.extraversion * 0.7 +
                       agent.personality.agreeableness * 0.3) * 10.0

        elif option == "rest":
            utility = 5.0 # Baseline

        return utility
