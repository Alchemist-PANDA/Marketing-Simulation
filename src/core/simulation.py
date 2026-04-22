"""
Base Simulation orchestration.
"""

from typing import Dict, Any, List
from .world import World
from .agent import Agent
from .decision_engine import DecisionEngine
from .social_graph import SocialGraph

class Simulation:
    def __init__(self, name: str, world_size: int = 100):
        self.world = World(name, world_size)
        self.decision_engine = DecisionEngine()
        self.social_graph = SocialGraph()
        self.steps_run = 0

    def step(self):
        """Main loop for one iteration of the entire simulation."""
        self.world.step()

        for agent_id, agent in self.world.agents.items():
            context = {
                "wealth": agent.state.money,
                "hour": self.world.current_time.hour
            }

            action = self.decision_engine.decide_action(agent, context, ["buy", "rest"])
            self._handle_action(agent, action)

        self.steps_run += 1

    def _handle_action(self, agent: Agent, action: str):
        if action == "buy":
            price = 10.0
            if agent.state.money >= price:
                agent.update_wealth(-price)
                agent.state.purchases.append({"time": self.world.current_time, "price": price})
                self.world.log_event("purchase", agent.id, {"price": price})
        else:
            self.world.log_event("rest", agent.id, {})

    def __repr__(self):
        return f"Simulation(steps={self.steps_run}, agents={len(self.world.agents)})"
