"""
Advanced behavioral psychology for agents.
No API calls. Pure math models of human decision-making biases.
"""

import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class CognitiveBias(Enum):
    """Behavioral economics biases implemented as modifiers"""
    ANCHORING = "anchoring"           # First price seen becomes reference
    LOSS_AVERSION = "loss_aversion"   # Fear of losing > joy of gaining
    HERDING = "herding"               # Follow the crowd
    SCARCITY = "scarcity"             # Limited availability boosts desire
    DECOY_EFFECT = "decoy"            # Third option makes target look better
    SUNK_COST = "sunk_cost"           # Already invested, keep going
    RECIPROCITY = "reciprocity"       # Free sample → feel obligated to buy
    AUTHORITY = "authority"           # Expert endorsement matters
    HYPERBOLIC_DISCOUNTING = "hyperbolic"  # Prefer immediate small reward
    MENTAL_ACCOUNTING = "mental_account"   # Money labeled for specific use


@dataclass
class PsychologicalState:
    """Dynamic psychological state that evolves during simulation"""

    # Emotional states (0-100)
    happiness: float = 50.0
    stress: float = 30.0
    excitement: float = 0.0
    trust: float = 50.0

    # Cognitive load
    decision_fatigue: float = 0.0      # More ads seen = harder to decide
    attention_budget: float = 100.0    # Depletes during day

    # Temporal effects
    morning_mood: float = 0.0          # +10 if morning person, -10 if night owl
    weekend_effect: float = 0.0        # Different spending on weekends

    # Social emotions
    envy: float = 0.0                  # Seeing friends with better things
    gratitude: float = 0.0             # After good deal
    regret: float = 0.0               # After bad purchase
    fomo: float = 0.0                # Fear of missing out

    # Memory effects
    peak_end_rule: Dict = field(default_factory=dict)  # Remember peak + end
    price_anchors: Dict[str, float] = field(default_factory=dict)  # Brand → anchor price


class BehavioralEconomicsEngine:
    """
    Applies behavioral economics principles to agent decisions.
    All models are mathematical formulations of Nobel Prize-winning research.
    """

    def __init__(self):
        self.bias_weights = {
            CognitiveBias.ANCHORING: 0.3,
            CognitiveBias.LOSS_AVERSION: 0.4,
            CognitiveBias.HERDING: 0.35,
            CognitiveBias.SCARCITY: 0.5,
            CognitiveBias.DECOY_EFFECT: 0.25,
            CognitiveBias.SUNK_COST: 0.2,
            CognitiveBias.RECIPROCITY: 0.3,
            CognitiveBias.AUTHORITY: 0.2,
            CognitiveBias.HYPERBOLIC_DISCOUNTING: 0.35,
            CognitiveBias.MENTAL_ACCOUNTING: 0.15
        }

    def apply_prospect_theory(self, agent, gain: float, loss: float) -> float:
        """
        Kahneman & Tversky Prospect Theory:
        Losses hurt ~2.25x more than equivalent gains feel good
        """
        lambda_loss = 2.25  # Loss aversion coefficient

        # Value function: v(x) = x^0.88 for gains, -lambda*(-x)^0.88 for losses
        if gain >= 0:
            value = gain ** 0.88
        else:
            value = -lambda_loss * ((-gain) ** 0.88)

        # Weight function: overweight small probabilities, underweight large ones
        def weight(p):
            return (p ** 0.65) / ((p ** 0.65 + (1-p) ** 0.65) ** (1/0.65))

        # Agent's personal loss aversion from neuroticism
        personal_lambda = lambda_loss * (0.5 + agent.personality.neuroticism * 0.5)

        return value * personal_lambda

    def apply_hyperbolic_discounting(self, agent, immediate_value: float,
                                   delayed_value: float, days_delay: int) -> float:
        """
        Agents prefer immediate rewards over larger delayed ones.
        Discount factor: 1 / (1 + k * delay)
        """
        # k varies by impulsiveness
        k = 0.1 + (1 - agent.personality.impulse_control) * 0.9

        immediate_utility = immediate_value
        delayed_utility = delayed_value / (1 + k * days_delay)

        return immediate_utility - delayed_utility

    def apply_herding(self, agent, brand: str, recent_purchases: int,
                     total_agents: int) -> float:
        """
        Social proof: more people buying → more likely to buy
        Uses logistic function for smooth transition
        """
        if total_agents == 0:
            return 0.0

        adoption_rate = recent_purchases / total_agents

        # Logistic: herding_effect = 1 / (1 + exp(-k*(rate - midpoint)))
        k = 10  # Steepness
        midpoint = 0.15  # 15% adoption triggers herding

        herding_effect = 1 / (1 + math.exp(-k * (adoption_rate - midpoint)))

        # Extraverts more susceptible
        susceptibility = 0.3 + agent.personality.extraversion * 0.7

        return herding_effect * susceptibility

    def apply_scarcity(self, agent, remaining_stock: int, total_stock: int,
                      time_remaining: int) -> float:
        """
        Scarcity heuristic: limited availability increases perceived value
        """
        if total_stock == 0:
            return 0.0

        stock_ratio = remaining_stock / total_stock
        time_pressure = 1 / (1 + time_remaining) if time_remaining > 0 else 1

        # Scarcity score: lower stock + less time = higher urgency
        scarcity_score = (1 - stock_ratio) * 0.6 + time_pressure * 0.4

        # Neurotic agents more responsive to scarcity (FOMO)
        fomo_factor = 0.5 + agent.personality.neuroticism * 0.5

        return scarcity_score * fomo_factor

    def apply_decoy_effect(self, agent, target_price: float,
                          competitor_price: float, decoy_price: Optional[float]) -> float:
        """
        Third option makes target look more attractive
        Classic: target=$400, competitor=$300, decoy=$450 (worse version of target)
        """
        if decoy_price is None:
            return 0.0

        # Decoy should be similar to target but slightly worse
        if decoy_price <= target_price:
            return 0.0  # Invalid decoy

        # Attraction effect: target looks better vs. decoy
        target_vs_competitor = competitor_price - target_price
        target_vs_decoy = decoy_price - target_price

        if target_vs_decoy > 0 and target_vs_competitor < target_vs_decoy:
            # Target is cheaper than decoy, close to competitor
            attraction = 0.3 * (1 - agent.personality.openness * 0.5)  # Less open = more susceptible
            return attraction

        return 0.0

    def apply_sunk_cost(self, agent, brand: str, total_spent: float) -> float:
        """
        Already invested → continue investing to "get value"
        """
        if total_spent < 50:  # Minimum threshold
            return 0.0

        # Diminishing returns: first $100 matters more than next $1000
        effect = math.log(1 + total_spent / 100) * 0.1

        # Conscientious agents more prone (they hate waste)
        susceptibility = 0.3 + agent.personality.conscientiousness * 0.4

        return min(0.3, effect * susceptibility)

    def apply_reciprocity(self, agent, free_value_received: float) -> float:
        """
        Received free sample/gift → feel obligated to buy
        """
        if free_value_received <= 0:
            return 0.0

        # Obligation scales with gift value (diminishing)
        obligation = math.log(1 + free_value_received) * 0.15

        # Agreeable agents more susceptible
        susceptibility = 0.3 + agent.personality.agreeableness * 0.7

        return min(0.4, obligation * susceptibility)

    def calculate_decision_fatigue(self, agent, ads_seen_today: int) -> float:
        """
        Baumeister's ego depletion: decisions get worse with fatigue
        """
        # Threshold: ~10 decisions before fatigue kicks in
        fatigue_threshold = 8 + agent.personality.conscientiousness * 8

        if ads_seen_today < fatigue_threshold:
            return 0.0

        # Post-threshold: linear increase in impulsiveness
        excess = ads_seen_today - fatigue_threshold
        fatigue_effect = min(0.5, excess * 0.05)

        return fatigue_effect

    def apply_peak_end_rule(self, agent, experiences: List[Dict]) -> float:
        """
        Kahneman's Peak-End Rule: remember peak intensity + final moment
        """
        if not experiences:
            return 0.0

        # Find peak (most intense) experience
        peak = max(experiences, key=lambda x: abs(x.get('intensity', 0)))
        peak_valence = peak.get('valence', 0)  # -1 to 1

        # Final experience
        end = experiences[-1]
        end_valence = end.get('valence', 0)

        # Weighted memory: 60% peak, 40% end
        memory_score = peak_valence * 0.6 + end_valence * 0.4

        return memory_score


class EmotionalEvolution:
    """
    Agent emotions evolve based on experiences.
    Creates realistic mood trajectories.
    """

    def __init__(self):
        self.decay_rates = {
            'happiness': 0.95,    # 5% decay per hour
            'stress': 0.90,       # Stress lingers
            'excitement': 0.80,   # Excitement fades fast
            'trust': 0.98,        # Trust changes slowly
            'envy': 0.85,
            'gratitude': 0.92,
            'regret': 0.88,
            'fomo': 0.75          # FOMO fades quickly if not reinforced
        }

    def update_emotions(self, state: PsychologicalState,
                       events: List[Dict], hour: int):
        """Apply emotional decay + event impacts"""

        # Decay existing emotions
        for emotion, rate in self.decay_rates.items():
            current = getattr(state, emotion)
            setattr(state, emotion, current * rate)

        # Apply event impacts
        for event in events:
            impact = event.get('emotional_impact', {})

            for emotion, delta in impact.items():
                current = getattr(state, emotion, 0)
                new_val = max(0, min(100, current + delta))
                setattr(state, emotion, new_val)

        # Time-of-day mood effects
        if 6 <= hour < 12:  # Morning
            state.morning_mood = 5 if state.happiness > 50 else -5
        elif hour >= 22 or hour < 6:  # Night
            state.stress *= 1.1  # Slightly more stressed at night

        # Weekend boost
        # (Would need day-of-week context)

        return state

    def get_mood_modifier(self, state: PsychologicalState) -> float:
        """Convert emotional state to decision modifier"""
        # Positive emotions increase buying, negative decrease
        positive = state.happiness + state.excitement + state.gratitude
        negative = state.stress + state.regret + state.envy

        net = (positive - negative) / 300  # Normalize

        # Bounded: -0.3 to +0.3 effect on purchase probability
        return max(-0.3, min(0.3, net))
