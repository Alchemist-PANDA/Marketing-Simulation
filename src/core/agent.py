# src/core/agent.py
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class Agent:
    def __init__(
        self,
        name: str,
        persona: Dict[str, Any],
        initial_wealth: float = 100.0,
        interests: List[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.persona = persona
        self.wealth = initial_wealth
        self.interests = interests or []
        self.inventory: Dict[str, int] = {}
        self.memory_keys: List[str] = []
        self.social_links: Dict[str, float] = {}  # agent_id -> relationship_strength
        self.created_at = datetime.now()

    def update_wealth(self, amount: float):
        self.wealth += amount

    def add_to_inventory(self, item_id: str, quantity: int = 1):
        self.inventory[item_id] = self.inventory.get(item_id, 0) + quantity

    def __repr__(self):
        return f"Agent(name={self.name}, wealth={self.wealth})"
