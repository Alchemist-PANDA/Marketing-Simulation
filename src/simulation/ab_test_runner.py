from typing import Dict, Any, List
from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation
from src.simulation.failure_analysis import analyze_failure

class ABTestRunner:
    def __init__(self, num_agents: int = 500, seed: int = None):
        self.num_agents = num_agents
        self.seed = seed
        self.sim = MaxSimulation(num_agents=num_agents, seed=seed)

    def run_test(self, ad_a_text: str, ad_b_text: str, channel: str = 'facebook', objective: str = 'conversions') -> Dict[str, Any]:
        ad_a = Ad(text=ad_a_text, channel=channel, creative_type='text', price=20.0)
        ad_b = Ad(text=ad_b_text, channel=channel, creative_type='text', price=20.0)

        res_a = self.sim.simulate_exposure(ad_a)

        # If we want independent runs for A and B with same agent population,
        # we might need to reset agents or use a new sim with same seed.
        # For now, we continue sequential exposure to the same population.
        res_b = self.sim.simulate_exposure(ad_b)

        # 1. Forensic Failure Analysis for both ads
        res_a['analysis'] = analyze_failure(
            ad_a.price_score, ad_a.trust_score, ad_a.urgency_score,
            ctr=res_a['likes'] / self.num_agents,
            cvr=res_a['conversions'] / max(1, res_a['likes'])
        )

        res_b['analysis'] = analyze_failure(
            ad_b.price_score, ad_b.trust_score, ad_b.urgency_score,
            ctr=res_b['likes'] / self.num_agents,
            cvr=res_b['conversions'] / max(1, res_b['likes'])
        )

        # 2. Comparison and Winner Selection based on objective
        val_a = res_a.get(objective, 0)
        val_b = res_b.get(objective, 0)

        # Calculate rates if requested
        if objective == 'conversion_rate':
            val_a = res_a['conversions'] / self.num_agents
            val_b = res_b['conversions'] / self.num_agents
        elif objective == 'engagement':
            val_a = (res_a['likes'] + res_a['shares']) / self.num_agents
            val_b = (res_b['likes'] + res_b['shares']) / self.num_agents

        winner = 'A' if val_a >= val_b else 'B'

        # Calculate lift percentage safely
        lift = 0.0
        loser_val = min(val_a, val_b)
        if loser_val > 0:
            lift = (abs(val_a - val_b) / loser_val) * 100
        elif max(val_a, val_b) > 0:
            lift = 100.0 # From 0 to something is 100% lift or infinity, we use 100 as cap

        return {
            'ad_a': res_a,
            'ad_b': res_b,
            'winner': winner,
            'lift_percentage': round(lift, 2),
            'objective': objective
        }
