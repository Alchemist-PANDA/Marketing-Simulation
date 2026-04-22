import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from scipy.stats import pearsonr
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad

def validate_public_ctr(num_agents=10000):
    print(f"Running Public CTR Validation with {num_agents} agents per ad...")

    if not os.path.exists('data/facebook_ads_real.csv'):
        print("Dataset not found. Run scripts/acquire_public_data.py first.")
        return

    df = pd.read_csv('data/facebook_ads_real.csv')
    sim = MaxSimulation(num_agents=num_agents)

    # Load calibrator if it exists
    calib = None
    if os.path.exists('models/calibrator.pkl'):
        with open('models/calibrator.pkl', 'rb') as f:
            calib = pickle.load(f)

    predicted_ctrs = []

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        # Full pipeline: NLP Scorer -> Psychographic Engine
        ad = Ad(text=row['ad_text'], channel="facebook", creative_type="text")
        res = sim.simulate_exposure(ad)

        raw_ctr = res['likes'] / num_agents
        raw_cvr = res['conversions'] / max(1, res['likes'])

        # Apply calibration if available
        if calib:
            adj_ctr, _, _ = calib.calibrate(raw_ctr, raw_cvr)
            predicted_ctrs.append(adj_ctr)
        else:
            predicted_ctrs.append(raw_ctr)

    df['predicted_ctr'] = predicted_ctrs

    # --- Step 3: Compute Metrics ---
    corr, p_val = pearsonr(df['actual_ctr'], df['predicted_ctr'])
    mae = np.mean(np.abs(df['actual_ctr'] - df['predicted_ctr']))
    rmse = np.sqrt(np.mean((df['actual_ctr'] - df['predicted_ctr'])**2))

    # Directional Accuracy (Pairwise Comparison)
    correct_rankings = 0
    total_pairs = 100
    np.random.seed(42)
    for _ in range(total_pairs):
        idx1, idx2 = np.random.choice(len(df), 2, replace=False)
        actual_winner = 1 if df.loc[idx1, 'actual_ctr'] > df.loc[idx2, 'actual_ctr'] else 2
        predicted_winner = 1 if df.loc[idx1, 'predicted_ctr'] > df.loc[idx2, 'predicted_ctr'] else 2

        if actual_winner == predicted_winner:
            correct_rankings += 1

    dir_acc = correct_rankings / total_pairs

    print(f"\n--- Public Validation Metrics ---")
    print(f"Pearson Correlation: {corr:.4f} (p={p_val:.4g})")
    print(f"Mean Absolute Error (MAE): {mae:.6f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.6f}")
    print(f"Directional Accuracy: {dir_acc:.2%}")

    # Plot
    os.makedirs('outputs', exist_ok=True)
    plt.figure(figsize=(10, 6))
    sns.regplot(data=df, x='actual_ctr', y='predicted_ctr', scatter_kws={'alpha':0.6})
    plt.title('Real-World CTR vs. Simulation Prediction')
    plt.xlabel('Actual CTR (Public Benchmarks)')
    plt.ylabel('Predicted CTR (Digital Wind Tunnel)')

    # Add diagonal reference line
    max_val = max(df['actual_ctr'].max(), df['predicted_ctr'].max())
    plt.plot([0, max_val], [0, max_val], '--', color='red', alpha=0.5, label='Perfect Prediction')
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.savefig('outputs/public_ctr_validation.png')
    print(f"Plot saved to outputs/public_ctr_validation.png")

    # --- Step 4: Evaluate 9/10 Criteria ---
    # Criteria: Correlation > 0.4 and MAE < 0.03
    if corr > 0.4 and mae < 0.03:
        print("\n[SUCCESS] 9/10 achieved - simulation predicts real-world CTR with acceptable accuracy.")
    else:
        print(f"\n[FAILURE] 9/10 not yet - need improvement. Correlation = {corr:.2f}, MAE = {mae:.4f}")

    return df, corr, mae

if __name__ == "__main__":
    validate_public_ctr()
