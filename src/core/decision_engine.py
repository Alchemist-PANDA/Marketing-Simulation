# src/core/decision_engine.py
from typing import Dict, Any, List
from .agent import Agent

class DecisionEngine:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name

    def decide_action(
        self,
        agent: Agent,
        context: Dict[str, Any],
        options: List[str]
    ) -> str:
        """
        Takes an agent, their current context, and available options,
        and uses logic or LLM to select an action.
        """
        # For a basic implementation, we just return a random action or a placeholder.
        # In a real scenario, this would involve prompting an LLM.
        if "buy" in options and agent.wealth > 20:
            return "buy"
        elif "interact" in options:
            return "interact"
        else:
            return options[0] if options else "idle"

    def evaluate_outcome(self, action: str, result: Dict[str, Any]) -> float:
        """
        Evaluate how successful an action was.
        """
        return result.get("utility", 0.0)
