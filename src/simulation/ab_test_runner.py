"""
A/B Test Runner with independent cohorts.
Eliminates order bias by splitting one generated population into two
disjoint cohorts via fancy indexing, with purchase state reset per cohort.
No agent-object deep copies — cohorts are NumPy array slices.
"""

from typing import Dict, Any
import numpy as np

from src.agents.agent_generator import generate_population_arrays
from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation
from src.simulation.failure_analysis import analyze_failure


class ABTestRunner:
    def __init__(self, num_agents: int = 500, seed: int = None, master_population: Dict[str, np.ndarray] = None):
        self.num_agents = num_agents
        self.seed = seed
        self.master_population = master_population

    def run_test(self, ad_a_text: str, ad_b_text: str,
                 channel: str = 'facebook', price: float = 20.0,
                 objective: str = 'conversions',
                 progress_callback=None) -> Dict[str, Any]:
        """
        Run an A/B test with strictly independent cohorts.

        Generates a single master population, splits it into two disjoint
        cohorts via a random permutation + fancy indexing (a copy, not a
        view, so mutating one cohort's money/purchase state can never leak
        into the other), and runs each ad against its own pristine cohort.
        """
        if self.master_population is not None:
            master = self.master_population
            self.num_agents = len(master['money'])
        else:
            master = generate_population_arrays(self.num_agents, seed=self.seed)

        rng = np.random.RandomState(self.seed)
        indices = rng.permutation(self.num_agents)
        mid = self.num_agents // 2

        idx_a = indices[:mid]
        idx_b = indices[mid:]

        cohort_a = {k: v[idx_a].copy() for k, v in master.items()}
        cohort_b = {k: v[idx_b].copy() for k, v in master.items()}

        seed_a = self.seed if self.seed is not None else None
        seed_b = (self.seed + 1) if self.seed is not None else None

        sim_a = MaxSimulation(seed=seed_a, population=cohort_a)
        sim_b = MaxSimulation(seed=seed_b, population=cohort_b)

        ad_a = Ad(text=ad_a_text, channel=channel, creative_type='text', price=price)
        ad_b = Ad(text=ad_b_text, channel=channel, creative_type='text', price=price)

        cb_a = None
        cb_b = None
        if progress_callback:
            def cb_a(pct, msg):
                progress_callback(pct * 0.45, f"Ad A: {msg}")
            def cb_b(pct, msg):
                progress_callback(0.5 + pct * 0.45, f"Ad B: {msg}")

        res_a = sim_a.simulate_exposure(ad_a, progress_callback=cb_a)
        if progress_callback:
            progress_callback(0.5, "Ad A complete, starting Ad B...")
        res_b = sim_b.simulate_exposure(ad_b, progress_callback=cb_b)

        cohort_a_size = sim_a.num_agents
        cohort_b_size = sim_b.num_agents

        ctr_a = res_a['likes'] / cohort_a_size
        cvr_a = res_a['conversions'] / max(1, res_a['likes'])
        ctr_b = res_b['likes'] / cohort_b_size
        cvr_b = res_b['conversions'] / max(1, res_b['likes'])

        res_a['analysis'] = analyze_failure(
            ad_a.price_score, ad_a.trust_score, ad_a.urgency_score,
            ctr=ctr_a, cvr=cvr_a
        )
        res_a['analysis']['predicted_ctr'] = round(ctr_a, 6)
        res_a['analysis']['predicted_cvr'] = round(cvr_a, 6)
        res_a['analysis']['confidence_score'] = 0.7
        res_a['cohort_size'] = cohort_a_size

        res_b['analysis'] = analyze_failure(
            ad_b.price_score, ad_b.trust_score, ad_b.urgency_score,
            ctr=ctr_b, cvr=cvr_b
        )
        res_b['analysis']['predicted_ctr'] = round(ctr_b, 6)
        res_b['analysis']['predicted_cvr'] = round(cvr_b, 6)
        res_b['analysis']['confidence_score'] = 0.7
        res_b['cohort_size'] = cohort_b_size

        val_a = res_a.get(objective, 0)
        val_b = res_b.get(objective, 0)

        if objective == 'conversion_rate':
            val_a = res_a['conversions'] / cohort_a_size
            val_b = res_b['conversions'] / cohort_b_size
        elif objective == 'engagement':
            val_a = (res_a['likes'] + res_a['shares']) / cohort_a_size
            val_b = (res_b['likes'] + res_b['shares']) / cohort_b_size

        winner = 'A' if val_a >= val_b else 'B'

        lift = 0.0
        loser_val = min(val_a, val_b)
        if loser_val > 0:
            lift = (abs(val_a - val_b) / loser_val) * 100
        elif max(val_a, val_b) > 0:
            lift = 100.0

        if progress_callback:
            progress_callback(1.0, "Analysis complete")

        return {
            'ad_a': res_a,
            'ad_b': res_b,
            'winner': winner,
            'lift_percentage': round(lift, 2),
            'objective': objective
        }
