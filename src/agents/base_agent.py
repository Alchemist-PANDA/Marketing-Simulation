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

    def __repr__(self):
        return f"Agent(name={self.name}, wealth={self.state.money:.2f}, extraversion={self.personality.extraversion})"

def create_persona_set(num_agents: int = 10) -> List[Agent]:
    """Generates a varied set of agent personalities"""
    agents = []
    names = ["Brian", "Linda", "Ian", "Sarah", "Kevin", "Mia", "James", "Elena", "Tom", "Chloe"]

    for i in range(num_agents):
        name = names[i % len(names)] if i < len(names) else f"Agent_{i}"

        # Varied personalities
        p = Personality(
            openness=random.random(),
            conscientiousness=random.random(),
            extraversion=random.random(),
            agreeableness=random.random(),
            neuroticism=random.random()
        )

        s = AgentState(money=random.uniform(50, 2000))
        agents.append(Agent(name=name, personality=p, initial_state=s))

    return agents
