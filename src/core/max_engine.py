"""
Maximum capability simulation engine.
Integrates all advanced modules into unified system.
Standalone implementation to ensure compatibility.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add src to path for relative imports to work
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.world import World
from core.agent import Agent
from core.decision_engine import DecisionEngine
from core.social_graph import SocialGraph
from core.advanced_psychology import BehavioralEconomicsEngine, EmotionalEvolution, PsychologicalState
from core.market_dynamics import NetworkEffects, SeasonalityEngine, BubbleDetector
from core.clv_churn import SurvivalModel, CLVEngine, ChurnInterventionEngine
from core.strategic_ai import PriceWarGame, MarketEntryGame, Strategy


class MaxSimulation:
    """
    Extended simulation with all advanced features.
    Standalone implementation including all core simulation logic.
    """

    def __init__(self, config_path: str, world_size: int = 100):
        self.world = World("MaxSim", world_size)
        self.decision_engine = DecisionEngine()
        self.social_graph = SocialGraph()
        self.steps_run = 0
        self.tick = 0

        # Advanced modules
        self.behavioral = BehavioralEconomicsEngine()
        self.emotional = EmotionalEvolution()
        self.network = NetworkEffects(self.world.agents)
        self.seasonality = SeasonalityEngine()
        self.bubble = BubbleDetector()
        self.survival = SurvivalModel()
        self.clv = CLVEngine(self.survival)
        self.intervention = ChurnInterventionEngine()

        # Track advanced metrics
        self.trends: list = []
        self.psychological_states: dict = {}

        # Load agents from config (Mock implementation for now)
        self._load_mock_agents()

    def _load_mock_agents(self):
        """Creates a set of initial agents for testing"""
        mock_agents = [
            ("Budget_Brian", {"price_sensitivity": 0.9, "brand_loyalty": 0.2, "neuroticism": 0.4, "extraversion": 0.3, "agreeableness": 0.5, "openness": 0.4, "ad_skepticism": 0.8, "social_influence": 0.2, "impulse_control": 0.9}, 50.0),
            ("Luxury_Linda", {"price_sensitivity": 0.1, "brand_loyalty": 0.8, "neuroticism": 0.2, "extraversion": 0.7, "agreeableness": 0.6, "openness": 0.8, "ad_skepticism": 0.2, "social_influence": 0.8, "impulse_control": 0.4}, 1000.0),
            ("Impulsive_Ian", {"price_sensitivity": 0.4, "brand_loyalty": 0.4, "neuroticism": 0.6, "extraversion": 0.8, "agreeableness": 0.4, "openness": 0.9, "ad_skepticism": 0.4, "social_influence": 0.6, "impulse_control": 0.1}, 200.0)
        ]
        for name, persona, wealth in mock_agents:
            # Create a simple MockPersonality object for compatibility
            class MockPersonality:
                def __init__(self, p):
                    for k, v in p.items():
                        setattr(self, k, v)

            agent = Agent(name, persona, wealth)
            agent.personality = MockPersonality(persona)
            # Ensure agent state has brand_affinity and purchases for CLV
            class MockState:
                def __init__(self):
                    self.brand_affinity = {}
                    self.purchases = []
                    self.money = wealth
                    self.happiness = 50.0
            agent.state = MockState()

            # Helper for deterministic random behavior
            import random
            def deterministic_random(seed):
                return random.Random(seed)
            agent.deterministic_random = deterministic_random

            self.world.add_agent(agent)
            self.psychological_states[name] = PsychologicalState()

    def initialize(self):
        """Initializes psychological states for all agents"""
        for name in self.world.agents:
            if name not in self.psychological_states:
                self.psychological_states[name] = PsychologicalState()

    def run(self, days: int = 1):
        """Runs the simulation for a specified number of days"""
        hours = days * 24
        for _ in range(hours):
            self.step()

    def step(self):
        """Advances simulation by one hour"""
        self.tick += 1
        day = self.tick // 24
        hour = self.tick % 24

        # Step the world
        self.world.step()

        # Update each agent
        for agent_id, agent in self.world.agents.items():
            # Update psychology
            state = self.psychological_states[agent_id]
            # Mock events list for now
            self.emotional.update_emotions(state, [], hour)

            # Simple decision logic
            context = {"hour": hour, "wealth": agent.wealth}
            action = self.decision_engine.decide_action(agent, context, ["buy", "rest"])

            if action == "buy":
                price = 15.0
                if agent.wealth >= price:
                    agent.update_wealth(-price)
                    agent.state.money = agent.wealth
                    agent.state.purchases.append({"day": day, "amount": price})
                    self.survival.record_activity(agent_id, day, "purchase", price)
                    self.world.log_event("purchase", agent_id, {"price": price})

        # Update network effects
        for brand in ['BrandA', 'BrandB']:
            self.network.calculate_critical_mass(brand)
            # Record for bubble detection
            adopters = sum(1 for a in self.world.agents.values() if a.state.brand_affinity.get(brand, 0) > 0.5)
            self.bubble.record(brand, 100.0, adopters)

        self.steps_run += 1

    def predict_clv(self, agent_name: str) -> dict:
        """Predict customer lifetime value"""
        pred = self.clv.calculate_clv(agent_name, self.tick // 24)
        return {
            "expected_ltv": pred.expected_ltv,
            "tenure": pred.expected_tenure_days,
            "churn_30d": pred.churn_probability_30d
        }

    def recommend_churn_intervention(self, agent_name: str) -> dict:
        """Get churn prevention recommendation"""
        clv_pred = self.clv.calculate_clv(agent_name, self.tick // 24)
        survival = self.survival.predict_survival(agent_name, self.tick // 24)

        return self.intervention.recommend_intervention(
            clv=clv_pred.expected_ltv,
            churn_risk=survival['churn_risk'],
            days_since_purchase=survival.get('days_active', 0)
        )

    def run_price_war_simulation(self, rounds: int = 50) -> dict:
        """Simulate strategic pricing game"""
        game = PriceWarGame(Strategy.TIT_FOR_TAT, Strategy.GRIM_TRIGGER)
        res = game.run_tournament(rounds)
        return {"winner": res["winner"], "score_a": res["final_score_a"], "score_b": res["final_score_b"]}

    def analyze_market_entry(self, entrant_cost_advantage: float = 0.2) -> dict:
        """Analyze if new brand should enter market"""
        entry = MarketEntryGame(
            incumbent_capacity=100,
            market_size=300,
            entry_cost=50,
            price_elasticity=1.5
        )
        return entry.analyze_entry(entrant_cost_advantage)

    def detect_market_trends(self) -> list:
        """Mock trend detection for testing"""
        return [{"type": "emerging_interest", "brand": "BrandA", "confidence": 0.85}]
