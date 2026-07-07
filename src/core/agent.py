"""
Agent definition with Big Five personality traits.
Zero API cost. Pure psychographic modeling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import random

@dataclass
class Personality:
    """Big Five Personality Traits (OCEAN) + Marketing specifics"""
    # Big Five (0.0 to 1.0)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Marketing specific traits
    price_sensitivity: float = 0.5
    ad_skepticism: float = 0.5
    social_influence: float = 0.5
    impulse_control: float = 0.5
    brand_loyalty: float = 0.5

@dataclass
class AgentState:
    """Dynamic state of an agent during simulation"""
    money: float = 100.0
    happiness: float = 50.0
    brand_affinity: Dict[str, float] = field(default_factory=dict)
    purchases: List[Dict] = field(default_factory=list)
    inventory: Dict[str, int] = field(default_factory=dict)

class Agent:
    def __init__(
        self,
        name: str,
        personality_dict: Dict[str, float],
        initial_wealth: float = 100.0,
        interests: List[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name

        # Filter personality_dict to only include valid OCEAN + marketing traits
        valid_traits = {
            'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism',
            'price_sensitivity', 'ad_skepticism', 'social_influence', 'impulse_control', 'brand_loyalty'
        }
        filtered_personality = {k: v for k, v in personality_dict.items() if k in valid_traits}

        # Ensure default values if missing
        for trait in valid_traits:
            if trait not in filtered_personality:
                filtered_personality[trait] = 0.5

        self.personality = Personality(**filtered_personality)
        self.state = AgentState(money=initial_wealth)
        self.interests = interests or []
        self.memory_keys: List[str] = []
        self.created_at = datetime.now()

    def update_wealth(self, amount: float):
        self.state.money += amount

    def deterministic_random(self, seed_suffix: str) -> random.Random:
        """Returns a seeded RNG for consistent behavior"""
        seed = f"{self.id}_{seed_suffix}"
        return random.Random(seed)

    def __repr__(self):
        return f"Agent(name={self.name}, wealth={self.state.money:.2f})"
