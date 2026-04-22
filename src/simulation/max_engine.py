"""
Primary Simulation Engine (MaxCap)
Integrates psychology, market dynamics, and ad engagement modeling.
Zero API cost design.
"""

import math
import random
from typing import Dict, List, Any
import numpy as np

from src.agents.base_agent import Agent, Personality, AgentState, create_persona_set
from src.psychology.prospect_theory import ProspectTheoryEngine
from src.psychology.emotional_response import EmotionEngine
from src.psychology.engagement_predictor import EngagementPredictor
from src.ad_processing.ad import Ad

class MaxSimulation:
    def __init__(self, num_agents: int = 100):
        self.agents = create_persona_set(num_agents)
        self.prospect = ProspectTheoryEngine()
        self.emotion = EmotionEngine()
        self.engagement = EngagementPredictor()
        self.tick = 0

    def simulate_exposure(self, ad: Ad) -> Dict[str, Any]:
        """Simulates one round of ad exposure to all agents"""
        round_results = {
            'likes': 0,
            'shares': 0,
            'conversions': 0,
            'details': []
        }

        for agent in self.agents:
            # 1. Emotional response
            emotional_mod = self.emotion.predict(agent.personality, ad)

            # 2. Archetype evaluation
            archetype_score = agent.evaluate_ad(ad)

            # 3. Compute utility via Prospect Theory
            # Base utility from price and quality
            price_disutility = self.prospect.apply(-ad.price, reference=0)

            # Perceived value combines emotional response and archetype fit
            perceived_value = 50.0 * (1 + emotional_mod + archetype_score)
            utility = perceived_value + price_disutility

            # 4. Decision to purchase
            # Convert utility to probability (logistic)
            prob_buy = 1 / (1 + math.exp(-utility / 10.0))
            bought = random.random() < prob_buy

            # 4. Engagement (Likes/Shares)
            like_prob = self.engagement.predict_like_probability(agent.personality, ad)
            share_prob = self.engagement.predict_share_probability(agent.personality, ad)

            liked = random.random() < like_prob
            shared = random.random() < share_prob

            if bought:
                agent.state.money -= ad.price
                agent.state.purchase_history.append({'ad': ad.text, 'price': ad.price})
                round_results['conversions'] += 1

            if liked: round_results['likes'] += 1
            if shared: round_results['shares'] += 1

        self.tick += 1
        return round_results
