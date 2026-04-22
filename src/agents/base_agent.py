from dataclasses import dataclass, field
from typing import Dict, Any, List
import random
import uuid

@dataclass
class Personality:
    """Big Five Personality Traits (OCEAN)"""
    openness: float          # 0-1
    conscientiousness: float # 0-1
    extraversion: float      # 0-1
    agreeableness: float     # 0-1
    neuroticism: float       # 0-1
    values: Dict[str, float] = field(default_factory=dict) # e.g., {'security':0.8, 'excitement':0.3}

@dataclass
class AgentState:
    money: float
    mood: float = 0.0          # -1 to 1, negative to positive
    last_ad_seen: str = None
    purchase_history: List[Dict] = field(default_factory=list)
    brand_affinity: Dict[str, float] = field(default_factory=dict)

class Agent:
    def __init__(self, name: str, personality: Personality, initial_state: AgentState):
        self.id = str(uuid.uuid4())
        self.name = name
        self.personality = personality
        self.state = initial_state

        # Sensitivity weights derived from personality (OCEAN)
        # Price: conscientious people are more careful with money
        self.price_sensitivity = personality.conscientiousness * 0.8

        # Trust: agreeable people value social proof/trust more
        self.trust_sensitivity = personality.agreeableness * 0.7

        # Urgency: extroverts and high-neuroticism agents are more FOMO-prone
        self.urgency_sensitivity = (personality.extraversion * 0.5 + personality.neuroticism * 0.4)

        # Skepticism: high neuroticism leads to general skepticism
        self.skepticism = personality.neuroticism * 0.3

    def evaluate_ad(self, ad: 'Ad') -> float:
        """
        Computes a weighted archetype score based on ad attributes.
        Returns a float where higher means more positive evaluation.
        """
        # Weighted sum of features
        weighted_score = (
            ad.price_score * self.price_sensitivity +
            ad.trust_score * self.trust_sensitivity +
            ad.urgency_score * self.urgency_sensitivity
        )

        # Subtract skepticism as a barrier
        return weighted_score - self.skepticism

    def __repr__(self):
        return f"Agent(name={self.name}, wealth={self.state.money:.2f}, extraversion={self.personality.extraversion})"

def create_archetype_agent(name: str, archetype: str) -> Agent:
    """Creates an agent with personality traits matching a specific archetype."""
    money = random.uniform(50, 2000)
    s = AgentState(money=money)

    if archetype == 'price_sensitive':
        p = Personality(
            openness=random.uniform(0.3, 0.6),
            conscientiousness=random.uniform(0.8, 1.0),
            extraversion=random.uniform(0.2, 0.5),
            agreeableness=random.uniform(0.4, 0.7),
            neuroticism=random.uniform(0.1, 0.4)
        )
    elif archetype == 'impulsive':
        p = Personality(
            openness=random.uniform(0.6, 0.9),
            conscientiousness=random.uniform(0.1, 0.4),
            extraversion=random.uniform(0.8, 1.0),
            agreeableness=random.uniform(0.4, 0.7),
            neuroticism=random.uniform(0.6, 0.9)
        )
    elif archetype == 'social_proof':
        p = Personality(
            openness=random.uniform(0.5, 0.8),
            conscientiousness=random.uniform(0.4, 0.7),
            extraversion=random.uniform(0.6, 0.9),
            agreeableness=random.uniform(0.8, 1.0),
            neuroticism=random.uniform(0.2, 0.5)
        )
    else: # skeptical
        p = Personality(
            openness=random.uniform(0.1, 0.4),
            conscientiousness=random.uniform(0.5, 0.8),
            extraversion=random.uniform(0.1, 0.4),
            agreeableness=random.uniform(0.1, 0.4),
            neuroticism=random.uniform(0.8, 1.0)
        )

    return Agent(name=name, personality=p, initial_state=s)

def generate_agents(n: int, distribution: Dict[str, float] = None, seed: int = None) -> List[Agent]:
    """
    Generate a population of n agents with a specific archetype distribution.
    Default distribution: 30% PriceSensitive, 25% Impulsive, 25% SocialProof, 20% Skeptical.
    """
    if seed is not None:
        random.seed(seed)

    if distribution is None:
        distribution = {
            'price_sensitive': 0.30,
            'impulsive': 0.25,
            'social_proof': 0.25,
            'skeptical': 0.20
        }

    types = []
    for agent_type, weight in distribution.items():
        count = int(n * weight)
        types.extend([agent_type] * count)

    # Fix rounding
    while len(types) < n:
        types.append(random.choice(list(distribution.keys())))
    while len(types) > n:
        types.pop()

    random.shuffle(types)

    agents = []
    for i, t in enumerate(types):
        agents.append(create_archetype_agent(f"Agent_{i}", t))

    return agents

def create_persona_set(num_agents: int = 10) -> List[Agent]:
    """Legacy helper: now uses the balanced archetype distribution"""
    return generate_agents(num_agents)
