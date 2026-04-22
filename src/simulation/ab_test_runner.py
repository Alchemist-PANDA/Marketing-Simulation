from typing import Dict, Any
from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation

class ABTestRunner:
    def __init__(self, num_agents: int = 500):
        self.sim = MaxSimulation(num_agents=num_agents)

    def run_test(self, ad_a_text: str, ad_b_text: str, channel: str = 'facebook') -> Dict[str, Any]:
        ad_a = Ad(text=ad_a_text, channel=channel, creative_type='text', price=20.0)
        ad_b = Ad(text=ad_b_text, channel=channel, creative_type='text', price=20.0)

        res_a = self.sim.simulate_exposure(ad_a)
        res_b = self.sim.simulate_exposure(ad_b)

        winner = 'A' if res_a['likes'] > res_b['likes'] else 'B'
        lift = 0.0
        if min(res_a['likes'], res_b['likes']) > 0:
            lift = (abs(res_a['likes'] - res_b['likes']) / min(res_a['likes'], res_b['likes'])) * 100

        return {
            'ad_a': res_a,
            'ad_b': res_b,
            'winner': winner,
            'lift_percentage': lift
        }
