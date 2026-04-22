import os
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad

def stability_test(n_runs=20, num_agents=5000):
    print(f"Running stability test: {n_runs} runs with {num_agents} agents...")

    ad = Ad(text="Fixed Stability Ad", channel="facebook", creative_type="text", price=10.0,
            price_score=0.7, trust_score=0.5, urgency_score=0.6)

    ctrs = []
    cvrs = []

    for i in tqdm(range(n_runs)):
        # MaxSimulation internally creates a new persona set each time
        sim = MaxSimulation(num_agents=num_agents)
        res = sim.simulate_exposure(ad)
        ctrs.append(res['likes'] / num_agents)
        cvrs.append(res['conversions'] / max(1, res['likes']))

    mean_ctr = np.mean(ctrs)
    std_ctr = np.std(ctrs)
    mean_cvr = np.mean(cvrs)
    std_cvr = np.std(cvrs)

    print(f"\n--- Stability Test Results ---")
    print(f"CTR: {mean_ctr:.4f} ± {std_ctr:.4f}")
    print(f"CVR: {mean_cvr:.4f} ± {std_cvr:.4f}")

    if std_ctr < 0.005:
        print("[SUCCESS] Stability within acceptable range (std < 0.005)")
    else:
        print("[WARNING] Stability warning: Standard deviation is higher than expected.")

if __name__ == "__main__":
    stability_test()
