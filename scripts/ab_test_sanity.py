import os
import sys
import numpy as np
from scipy import stats

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.ab_test_runner import ABTestRunner

def ab_test_sanity():
    print("Running A/B Test Sanity Check...")

    # Ad A: High scores across the board
    ad_a_text = "Save 90% today! Trusted by millions. Limited time offer!"
    # We will manually set scores for the simulation call to ensure contrast

    # Ad B: Low scores across the board
    ad_b_text = "Expensive product. No reviews. Available forever."

    num_agents = 2000
    runner = ABTestRunner(num_agents=num_agents)

    # Note: run_test creates Ad objects. We want to ensure the scores are what we expect.
    # Ad A: P:0.9, T:0.8, U:0.9
    # Ad B: P:0.2, T:0.2, U:0.2

    # Since run_test doesn't allow passing scores, we'll implement a localized version
    # to ensure the sanity check is testing the engine's core logic properly.

    from src.ad_processing.ad import Ad

    ad_a = Ad(text=ad_a_text, channel="facebook", creative_type="text", price=10.0,
              price_score=0.9, trust_score=0.8, urgency_score=0.9)
    ad_b = Ad(text=ad_b_text, channel="facebook", creative_type="text", price=10.0,
              price_score=0.2, trust_score=0.2, urgency_score=0.2)

    # Get results
    res_a = runner.sim.simulate_exposure(ad_a)
    res_b = runner.sim.simulate_exposure(ad_b)

    likes_a = res_a['likes']
    likes_b = res_b['likes']

    ctr_a = likes_a / num_agents
    ctr_b = likes_b / num_agents

    lift = ((ctr_a - ctr_b) / max(0.001, ctr_b)) * 100

    # Simple T-test for proportions
    # Pooled proportion
    p_pool = (likes_a + likes_b) / (2 * num_agents)
    se = np.sqrt(p_pool * (1 - p_pool) * (2 / num_agents))
    z = (ctr_a - ctr_b) / max(1e-10, se)
    p_val = 1 - stats.norm.cdf(abs(z))

    print(f"\n--- A/B Test Sanity Results ---")
    print(f"Ad A CTR: {ctr_a:.4f} ({likes_a} likes)")
    print(f"Ad B CTR: {ctr_b:.4f} ({likes_b} likes)")
    print(f"Lift: {lift:.2f}%")
    print(f"P-value: {p_val:.6f}")

    if p_val < 0.05 and lift > 50:
        print("[SUCCESS] A/B Test Sanity Check Passed")
    else:
        print("[FAILURE] A/B Test Sanity Check Failed")

if __name__ == "__main__":
    ab_test_sanity()
