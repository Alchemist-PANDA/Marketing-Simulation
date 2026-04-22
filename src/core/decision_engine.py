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
        agent: Agent,
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
