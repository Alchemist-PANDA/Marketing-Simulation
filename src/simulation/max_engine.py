"""
Primary Simulation Engine (MaxCap)
Integrates psychology, market dynamics, and ad engagement modeling.
Zero API cost design. NumPy-vectorized for 10k+ agent throughput.
"""

import json
import os
from typing import Dict, List, Any, Optional
import numpy as np

from src.agents.base_agent import Agent, Personality, AgentState, create_persona_set
from src.psychology.prospect_theory import ProspectTheoryEngine
from src.ad_processing.ad import Ad


class MaxSimulation:
    def __init__(self, num_agents: int = 100, seed: int = None, agents: List[Agent] = None):
        self.seed = seed
        self.np_rng = np.random.RandomState(seed)
        self.prospect = ProspectTheoryEngine()
        self.tick = 0

        if agents is not None:
            self.agents = agents
            self.num_agents = len(agents)
        else:
            self.agents = create_persona_set(num_agents, seed=seed)
            self.num_agents = num_agents

        self.archetype_calibration = {}
        config_path = 'config/archetype_calibration.json'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.archetype_calibration = json.load(f)
            except Exception:
                pass

        self._precompute_arrays()

    def _precompute_arrays(self):
        """Extract agent traits into NumPy arrays for vectorized operations."""
        agents = self.agents
        self._extraversion = np.array([a.personality.extraversion for a in agents])
        self._conscientiousness = np.array([a.personality.conscientiousness for a in agents])
        self._openness = np.array([a.personality.openness for a in agents])
        self._agreeableness = np.array([a.personality.agreeableness for a in agents])
        self._neuroticism = np.array([a.personality.neuroticism for a in agents])
        self._price_sensitivity = np.array([a.price_sensitivity for a in agents])
        self._trust_sensitivity = np.array([a.trust_sensitivity for a in agents])
        self._urgency_sensitivity = np.array([a.urgency_sensitivity for a in agents])
        self._skepticism = np.array([a.skepticism for a in agents])
        self._money = np.array([a.state.money for a in agents])
        self._cal_factors = np.array([
            self.archetype_calibration.get(a.archetype, 1.0) for a in agents
        ])

    def simulate_exposure(self, ad: Ad, progress_callback=None) -> Dict[str, Any]:
        """Simulates one round of ad exposure to all agents using vectorized NumPy ops."""
        n = self.num_agents

        # 1. Emotional response (vectorized channel/creative modifiers)
        emotional_mod = np.zeros(n)
        if ad.channel in ('facebook', 'tiktok', 'instagram'):
            emotional_mod += self._extraversion * 0.3
        if ad.channel in ('google', 'search', 'email'):
            emotional_mod += self._conscientiousness * 0.4
        if ad.creative_type in ('video', 'flashy'):
            emotional_mod -= self._neuroticism * 0.5
        if ad.creative_type in ('video', 'interactive'):
            emotional_mod += self._openness * 0.4
        np.clip(emotional_mod, -1.0, 1.0, out=emotional_mod)

        if progress_callback:
            progress_callback(0.2, "Emotional analysis complete")

        # 2. Archetype evaluation (vectorized dot product)
        archetype_score = (
            ad.price_score * self._price_sensitivity
            + ad.trust_score * self._trust_sensitivity
            + ad.urgency_score * self._urgency_sensitivity
            - self._skepticism
        )

        # 3. Prospect theory price disutility (scalar, applied to all)
        price_disutility = self.prospect.apply(-ad.price, reference=0)

        # 4. Utility calculation
        fomo_impact = ad.urgency_score * 0.5
        perceived_value = 10.0 * (1.0 + emotional_mod + archetype_score + fomo_impact)
        utility = perceived_value + price_disutility

        if progress_callback:
            progress_callback(0.4, "Utility calculation complete")

        # 5. Purchase probability (vectorized sigmoid)
        prob_buy = 1.0 / (1.0 + np.exp(np.clip(-utility / 10.0, -500, 500)))

        # 6. Affordability gate
        can_afford = self._money >= ad.price
        prob_buy *= can_afford

        # 7. Engagement probabilities (vectorized)
        like_prob = (
            0.1
            + self._extraversion * 0.2
            + self._openness * 0.1
            - self._neuroticism * 0.05
            + ad.price_score * 0.1
            + ad.trust_score * 0.25
            + ad.urgency_score * 0.4
        )
        if ad.channel in ('tiktok', 'instagram'):
            like_prob *= 1.5
        like_prob *= self._cal_factors
        np.clip(like_prob, 0, 1, out=like_prob)

        share_prob = np.clip(
            0.05 + 0.5 * self._extraversion + 0.1 * self._agreeableness,
            0, 1
        )

        if progress_callback:
            progress_callback(0.6, "Probability models complete")

        # 8. Vectorized binomial sampling
        rand_buy = self.np_rng.random(n)
        rand_like = self.np_rng.random(n)
        rand_share = self.np_rng.random(n)

        bought = rand_buy < prob_buy
        liked = rand_like < like_prob
        shared = rand_share < share_prob

        if progress_callback:
            progress_callback(0.8, "Agent decisions sampled")

        # 9. Update agent state for purchases (minimal loop, only purchasers)
        purchase_indices = np.where(bought)[0]
        for idx in purchase_indices:
            self.agents[idx].state.money -= ad.price
            self.agents[idx].state.purchase_history.append({
                'ad': ad.text, 'price': ad.price
            })
        self._money[purchase_indices] -= ad.price

        if progress_callback:
            progress_callback(1.0, "Simulation complete")

        self.tick += 1

        return {
            'likes': int(liked.sum()),
            'shares': int(shared.sum()),
            'conversions': int(bought.sum()),
            'details': []
        }
