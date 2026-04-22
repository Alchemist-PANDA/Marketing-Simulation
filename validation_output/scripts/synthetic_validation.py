import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad

def synthetic_validation(n_ads=100, num_agents=2000):
    print(f"Running synthetic validation with {n_ads} ads and {num_agents} agents per ad...")

    # True model parameters (representing 'reality')
    # true_ctr = 0.03 + 0.4*price_score + 0.3*trust_score + 0.2*urgency_score + noise
    # Note: These weights should be higher than our engine's defaults to test if it detects the same directionality

    results = []
    sim = MaxSimulation(num_agents=num_agents)

    os.makedirs('outputs', exist_ok=True)

    for i in tqdm(range(n_ads)):
        # Generate random scores
        price_score = np.random.uniform(0.1, 0.9)
        trust_score = np.random.uniform(0.1, 0.9)
        urgency_score = np.random.uniform(0.1, 0.9)

        # 1. Define 'true' CTR (Reality)
        true_ctr = 0.02 + 0.05 * price_score + 0.03 * trust_score + 0.02 * urgency_score + np.random.normal(0, 0.002)
        true_ctr = max(0.001, min(0.1, true_ctr))

        # 2. Predicted CTR (Simulation)
        # Create ad and run simulation
        # Note: We need to override price_score/trust_score/urgency_score manually to test sensitivity
        ad = Ad(text=f"Validation Ad {i}", channel="facebook", creative_type="text", price=10.0,
                price_score=price_score, trust_score=trust_score, urgency_score=urgency_score)

        res = sim.simulate_exposure(ad)
        predicted_ctr = res['likes'] / num_agents

        results.append({
            'ad_id': i,
            'price_score': price_score,
            'trust_score': trust_score,
            'urgency_score': urgency_score,
            'true_ctr': true_ctr,
            'predicted_ctr': predicted_ctr
        })

    df = pd.DataFrame(results)

    # 3. Compute Metrics
    mae = np.mean(np.abs(df['true_ctr'] - df['predicted_ctr']))
    rmse = np.sqrt(np.mean((df['true_ctr'] - df['predicted_ctr'])**2))
    corr, p_val = pearsonr(df['true_ctr'], df['predicted_ctr'])

    print(f"\n--- Synthetic Validation Metrics ---")
    print(f"Mean Absolute Error (MAE): {mae:.6f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.6f}")
    print(f"Pearson Correlation: {corr:.4f} (p={p_val:.4g})")

    # 4. Generate Plot
    plt.figure(figsize=(10, 6))
    sns.regplot(data=df, x='true_ctr', y='predicted_ctr', scatter_kws={'alpha':0.5})
    plt.title('Synthetic Ground Truth vs. Simulation Prediction (CTR)')
    plt.xlabel('True CTR (Reality)')
    plt.ylabel('Predicted CTR (Simulation)')
    plt.grid(True, alpha=0.3)
    plt.savefig('outputs/synthetic_validation.png')
    print(f"Scatter plot saved to outputs/synthetic_validation.png")

    return df, mae, corr

if __name__ == "__main__":
    synthetic_validation(n_ads=50, num_agents=2000)
