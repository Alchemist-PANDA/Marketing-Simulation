"""
Primary Simulation Engine (MaxCap)
Integrates psychology, market dynamics, and ad engagement modeling.
Zero API cost design.
"""

import math
import random
import json
import os
from typing import Dict, List, Any
import numpy as np

from src.agents.base_agent import Agent, Personality, AgentState, create_persona_set
from src.psychology.prospect_theory import ProspectTheoryEngine
from src.psychology.emotional_response import EmotionEngine
from src.psychology.engagement_predictor import EngagementPredictor
from src.ad_processing.ad import Ad

class MaxSimulation:
    def __init__(self, num_agents: int = 100):
        self.num_agents = num_agents
        self.agents = create_persona_set(num_agents)
        self.prospect = ProspectTheoryEngine()
        self.emotion = EmotionEngine()
        self.engagement = EngagementPredictor()
        self.tick = 0

        # Default weights (uncalibrated)
        self.weights = {
            'w_emotional': 1.0,
            'w_archetype': 1.0,
            'w_fomo': 0.5,
            'w_trust': 0.5,
            'w_price': 0.05,
            'bias': -4.0,
            'sigmoid_scale': 1.0
        }

        # Load optimized weights if available
        weights_path = 'config/simulation_weights.json'
        if os.path.exists(weights_path):
            with open(weights_path, 'r') as f:
                self.weights.update(json.load(f))
                print(f"Loaded calibrated weights from {weights_path}")

    def simulate_exposure(self, ad: Ad) -> Dict[str, Any]:
        """Simulates one round of ad exposure to all agents"""
        round_results = {
            'likes': 0,
            'shares': 0,
            'conversions': 0,
            'details': []
        }

        w = self.weights

        for agent in self.agents:
            # 1. Emotional response
            emotional_mod = self.emotion.predict(agent.personality, ad)

            # 2. Archetype evaluation
            archetype_score = agent.evaluate_ad(ad)

            # 3. Compute utility
            # Base price disutility from prospect theory
            # price_disutility = self.prospect.apply(-ad.price, reference=0)
            price_disutility = -ad.price / 10.0 # Simpler linear price impact

            # Weighted utility calculation (Calibrated)
            utility = (
                w['w_emotional'] * emotional_mod +
                w['w_archetype'] * archetype_score +
                w['w_fomo'] * ad.urgency_score +
                w['w_trust'] * ad.trust_score +
                w['w_price'] * price_disutility +
                w['bias']
            )

            # 4. Decision to purchase (Conversion)
            prob_buy = 1 / (1 + math.exp(-utility / w['sigmoid_scale']))
            bought = random.random() < prob_buy

            # 4. Engagement (Likes/Shares)
            like_prob = 1 / (1 + math.exp(-utility / w['sigmoid_scale'])) # Use utility for likes too
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
