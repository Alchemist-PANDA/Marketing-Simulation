import os
import json
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from scipy.stats import pearsonr
from tqdm import tqdm
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad

def run_sim_with_weights(weights, ads, num_agents=2000):
    """
    Runs a simplified version of simulate_exposure to collect utility components.
    weights: [w_emotional, w_archetype, w_fomo, w_trust, w_price, bias, sigmoid_scale]
    """
    w_emotional, w_archetype, w_fomo, w_trust, w_price, bias, sigmoid_scale = weights

    # Sigmoid scale should not be zero or negative
    sigmoid_scale = max(0.1, sigmoid_scale)

    predicted_ctrs = []

    # We use a subset of agents for speed during calibration
    sim = MaxSimulation(num_agents=num_agents)

    for ad in ads:
        total_prob = 0
        for agent in sim.agents:
            emotional_mod = sim.emotion.predict(agent.personality, ad)
            archetype_score = agent.evaluate_ad(ad)
            # price_disutility = sim.prospect.apply(-ad.price, reference=0)
            price_disutility = -ad.price / 10.0

            # Weighted utility
            utility = (
                w_emotional * emotional_mod +
                w_archetype * archetype_score +
                w_fomo * ad.urgency_score +
                w_trust * ad.trust_score +
                w_price * price_disutility +
                bias
            )

            prob = 1 / (1 + np.exp(-utility / sigmoid_scale))
            total_prob += prob

        predicted_ctrs.append(total_prob / num_agents)

    return np.array(predicted_ctrs)

def objective(weights, ads, actual_ctrs):
    preds = run_sim_with_weights(weights, ads)

    # We want to maximize correlation, which is minimizing -correlation
    if np.std(preds) == 0:
        return 0

    corr, _ = pearsonr(actual_ctrs, preds)

    # Also include MSE to ensure the magnitude is correct (1-3% CTR)
    mse = np.mean((actual_ctrs - preds)**2)

    # Loss = (1 - correlation) + 100 * MSE
    # (MSE is multiplied by 100 because CTRs are small, e.g., 0.02^2 = 0.0004)
    return (1 - corr) + 100 * mse

def calibrate():
    print("Starting ABM Calibration...")

    # 1. Load calibration data
    if not os.path.exists('data/real_ctr.csv'):
        print("Error: data/real_ctr.csv not found. Run create_real_ctr_data.py first.")
        return

    df = pd.read_csv('data/real_ctr.csv').head(50) # Use 50 ads for calibration
    ads = [Ad(text=row['ad_text'], channel='facebook', creative_type='text') for _, row in df.iterrows()]
    actual_ctrs = df['actual_ctr'].values

    # 2. Initial weights
    # [w_emotional, w_archetype, w_fomo, w_trust, w_price, bias, sigmoid_scale]
    initial_weights = [1.0, 1.0, 0.5, 0.5, 0.05, -4.0, 1.0]

    # 3. Optimize
    print("Optimizing weights (this may take a few minutes)...")
    res = minimize(
        objective,
        initial_weights,
        args=(ads, actual_ctrs),
        method='Nelder-Mead',
        options={'maxiter': 200, 'disp': True}
    )

    opt_weights = res.x
    labels = ['w_emotional', 'w_archetype', 'w_fomo', 'w_trust', 'w_price', 'bias', 'sigmoid_scale']
    weight_dict = dict(zip(labels, opt_weights.tolist()))

    print("\n--- Optimized Weights ---")
    for k, v in weight_dict.items():
        print(f"{k}: {v:.4f}")

    # 4. Save to config
    os.makedirs('config', exist_ok=True)
    with open('config/simulation_weights.json', 'w') as f:
        json.dump(weight_dict, f, indent=4)
    print("\nWeights saved to config/simulation_weights.json")

if __name__ == "__main__":
    calibrate()
