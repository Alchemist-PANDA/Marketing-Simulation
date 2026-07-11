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
                 ad_c_text: str = None,
                 channel: str = 'facebook', price: float = 20.0,
                 objective: str = 'conversions',
                 visual_quality: Dict[str, float] = None,
                 progress_callback=None) -> Dict[str, Any]:
        """
        Run an A/B (or A/B/C) test with strictly independent cohorts.

        Generates a single master population and splits it into N disjoint
        cohorts (2 or 3) via a random permutation + fancy indexing (a copy, not
        a view, so mutating one cohort's money/purchase state can never leak into
        another). Each ad runs against its own pristine cohort.

        ``ad_c_text`` is optional: when omitted the output is identical to the
        classic two-variant A/B test (keys ``ad_a``/``ad_b``). When provided, a
        third cohort is added and the result also carries ``ad_c`` plus a
        ``variants`` list; ``winner`` is the best of all three.
        """
        # Assemble variants (2 or 3). Labels stay A/B/C for the UI.
        variant_texts = [('A', ad_a_text), ('B', ad_b_text)]
        if ad_c_text and str(ad_c_text).strip():
            variant_texts.append(('C', ad_c_text))
        n = len(variant_texts)

        if self.master_population is not None:
            master = self.master_population
            self.num_agents = len(master['money'])
        else:
            master = generate_population_arrays(self.num_agents, seed=self.seed)

        rng = np.random.RandomState(self.seed)
        indices = rng.permutation(self.num_agents)
        # Split into n roughly-equal disjoint cohorts.
        splits = np.array_split(indices, n)

        results = {}          # label -> res dict
        values = {}           # label -> objective value
        for i, (label, text) in enumerate(variant_texts):
            cohort = {k: v[splits[i]].copy() for k, v in master.items()}
            seed_i = (self.seed + i) if self.seed is not None else None
            sim = MaxSimulation(seed=seed_i, population=cohort)
            ad = Ad(text=text, channel=channel, creative_type='text', price=price)

            cb = None
            if progress_callback:
                lo = i / n
                span = 1.0 / n

                def cb(pct, msg, _lo=lo, _span=span, _label=label):
                    progress_callback(_lo + pct * _span, f"Ad {_label}: {msg}")

            res = sim.simulate_exposure(ad, progress_callback=cb)
            size = sim.num_agents
            ctr = res['likes'] / size
            cvr = res['conversions'] / max(1, res['likes'])
            res['analysis'] = analyze_failure(
                ad.price_score, ad.trust_score, ad.urgency_score, ctr=ctr, cvr=cvr
            )
            res['analysis']['predicted_ctr'] = round(ctr, 6)
            res['analysis']['predicted_cvr'] = round(cvr, 6)
            res['analysis']['confidence_score'] = min(1.0, size / 500)
            res['cohort_size'] = size

            if objective == 'conversion_rate':
                val = res['conversions'] / size
            elif objective == 'engagement':
                val = (res['likes'] + res['shares']) / size
            else:
                val = res.get(objective, 0)

            results[label] = res
            values[label] = val

        # Winner = highest objective value; lift = best vs runner-up.
        ranked = sorted(values, key=lambda k: values[k], reverse=True)
        winner = ranked[0]
        best_val = values[ranked[0]]
        second_val = values[ranked[1]]
        if second_val > 0:
            lift = (abs(best_val - second_val) / second_val) * 100
        elif best_val > 0:
            lift = 100.0
        else:
            lift = 0.0

        if progress_callback:
            progress_callback(1.0, "Analysis complete")

        out = {
            'ad_a': results['A'],
            'ad_b': results['B'],
            'winner': winner,
            'winner_source': 'simulation',
            'lift_percentage': round(lift, 2),
            'objective': objective,
        }
        if 'C' in results:
            out['ad_c'] = results['C']
            out['variants'] = [lbl for lbl, _ in variant_texts]

        # Learned creative ranker (validated against real TikTok Creative
        # Center outcomes). When it makes a confident call, its pick
        # overrides the simulation heuristic; when the race is too close,
        # we say so instead of faking certainty.
        try:
            from src.ai import creative_ranker as cr
            if cr.is_available():
                tmap = dict(variant_texts)
                # visual_quality: {label: visual feature dict} (or legacy float)
                vis = {}
                for lbl, v in (visual_quality or {}).items():
                    vis[lbl] = v if isinstance(v, dict) else (
                        {"visual_quality": float(v), "available": True}
                        if v is not None else None)
                qualities = {
                    lbl: cr.score_ad(text, visual=vis.get(lbl))
                    for lbl, text in variant_texts
                }
                q_ranked = sorted(qualities, key=qualities.get, reverse=True)
                top1, top2 = q_ranked[0], q_ranked[1]
                verdict = cr.compare(tmap[top1], tmap[top2],
                                     visual_a=vis.get(top1),
                                     visual_b=vis.get(top2))
                ranker_winner = top1 if verdict['winner'] == 'A' else top2
                out['ranker'] = {
                    'available': True,
                    'winner': ranker_winner,
                    'confidence': verdict['confidence'],
                    'called': verdict['called'],
                    'threshold': verdict['threshold'],
                    'qualities': {k: round(v, 4) for k, v in qualities.items()},
                }
                if verdict['called']:
                    out['winner'] = ranker_winner
                    out['winner_source'] = 'validated_model'
                else:
                    out['winner_source'] = 'too_close_to_call'
        except Exception:
            out['ranker'] = {'available': False}

        return out
