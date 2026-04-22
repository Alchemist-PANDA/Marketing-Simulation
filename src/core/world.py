# src/core/world.py
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .agent import Agent

class World:
    def __init__(self, name: str, size: int = 100):
        self.name = name
        self.size = size
        self.current_time = datetime(2024, 1, 1, 0, 0, 0)
        self.agents: Dict[str, Agent] = {}
        self.events: List[Dict[str, Any]] = []

    def add_agent(self, agent: Agent):
        self.agents[agent.id] = agent

    def get_agent(self, agent_id: str) -> Agent:
        return self.agents.get(agent_id)

    def step(self, delta_minutes: int = 60):
        """
        Advance the world's internal time.
        """
        self.current_time += timedelta(minutes=delta_minutes)

    def log_event(self, event_type: str, actor_id: str, data: Dict[str, Any]):
        """
        Record significant events that happen in the world.
        """
        self.events.append({
            "timestamp": self.current_time,
            "type": event_type,
            "actor": actor_id,
            "data": data
        })

    def __repr__(self):
        return f"World(name={self.name}, agents={len(self.agents)}, time={self.current_time})"
