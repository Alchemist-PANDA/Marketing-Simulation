import os
import sys
import unittest
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestFullProject(unittest.TestCase):
    """
    End-to-end testing for the full marketing simulation project.
    Validates components integration and simulation flow.
    """

    def setUp(self):
        print(f"\nPHASE: Initializing E2E Test - {datetime.now().strftime('%H:%M:%S')}")
        self.test_config = {
            "duration": 7,
            "budget": 5000,
            "segments": ["Tech Enthusiasts", "Budget Conscious"]
        }

    def test_01_imports(self):
        print("PHASE: Testing core component imports...")
        try:
            from src.core.simulation import Simulation
            from src.core.agent import Agent
            from src.core.decision_engine import DecisionEngine
            print("OK: Core imports successful")
        except ImportError as e:
            self.fail(f"FAIL: Import failed: {str(e)}")

    def test_02_data_structures(self):
        print("PHASE: Validating data directory and structures...")
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.assertTrue(os.path.exists(data_dir), "FAIL: Data directory missing")
        print("OK: Data structures validated")

    def test_03_engine_logic(self):
        print("PHASE: Testing decision engine core logic...")
        from src.core.decision_engine import DecisionEngine
        from src.core.agent import Agent

        engine = DecisionEngine()
        agent = Agent("test_agent", {"persona": "frugal"})

        # Test action decision
        context = {"wealth": 100, "inventory": []}
        options = ["buy", "rest"]
        action = engine.decide_action(agent, context, options)

        self.assertIn(action, options)
        print("OK: Decision engine logic verified")

    def test_04_full_simulation_run(self):
        print("PHASE: Running mini-simulation (7 steps)...")
        from src.core.simulation import Simulation

        sim = Simulation("TestSim", world_size=10)
        sim.add_agent("Agent1", {"type": "consumer"})

        for _ in range(7):
            sim.step()

        self.assertEqual(sim.steps_run, 7)
        print("OK: Mini-simulation run completed successfully")

    def tearDown(self):
        print(f"RESULTS: Test completed at {datetime.now().strftime('%H:%M:%S')}\n")

if __name__ == "__main__":
    unittest.main()
