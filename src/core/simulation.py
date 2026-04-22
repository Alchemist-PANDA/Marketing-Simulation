# src/core/simulation.py
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

    def add_agent(
        self,
        name: str,
        persona: Dict[str, Any],
        initial_wealth: float = 100.0,
        interests: List[str] = None
    ) -> Agent:
        agent = Agent(name, persona, initial_wealth, interests)
        self.world.add_agent(agent)
        return agent

    def step(self):
        """
        Main loop for one iteration of the entire simulation.
        """
        # Step the world time forward
        self.world.step()

        # Update and iterate through all agents
        for agent_id, agent in self.world.agents.items():
            # Get current context
            context = {
                "world_time": self.world.current_time,
                "wealth": agent.wealth,
                "inventory": agent.inventory,
                "nearby_agents": self.social_graph.get_neighbors(agent_id),
                "recent_events": self.world.events[-5:] if self.world.events else []
            }

            # Decision making
            options = ["buy", "interact", "rest"]
            action = self.decision_engine.decide_action(agent, context, options)

            # Execution
            self._handle_action(agent, action)

        self.steps_run += 1

    def _handle_action(self, agent: Agent, action: str):
        """
        Processes individual agent actions and logs them.
        """
        if action == "buy":
            # Simple purchase logic
            price = 10.0
            if agent.wealth >= price:
                agent.update_wealth(-price)
                agent.add_to_inventory("basic_good")
                self.world.log_event("purchase", agent.id, {"item": "basic_good", "price": price})
        elif action == "interact":
            # Dummy logic for interaction
            self.world.log_event("social_interaction", agent.id, {"type": "chat"})
        else:
            # Idle/Rest
            self.world.log_event("idle", agent.id, {})

    def __repr__(self):
        return (f"Simulation(name={self.world.name}, steps={self.steps_run}, "
                f"agents={len(self.world.agents)})")
