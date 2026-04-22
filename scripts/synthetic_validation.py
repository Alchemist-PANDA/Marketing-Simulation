import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from scipy.stats import pearsonr
from tqdm import tqdm
from sklearn.model_selection import train_test_split

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad
from src.simulation.calibrator import Calibrator

def synthetic_validation(n_ads=100, num_agents=2000):
    print(f"Running calibrated synthetic validation with {n_ads} ads...")

    results = []
    sim = MaxSimulation(num_agents=num_agents)
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('models', exist_ok=True)

    for i in tqdm(range(n_ads)):
        price_score = np.random.uniform(0.1, 0.9)
        trust_score = np.random.uniform(0.1, 0.9)
        urgency_score = np.random.uniform(0.1, 0.9)

        # True model (Reality)
        true_ctr = 0.02 + 0.05 * price_score + 0.03 * trust_score + 0.02 * urgency_score + np.random.normal(0, 0.002)
        true_ctr = max(0.001, min(0.1, true_ctr))

        # Simplified CVR reality
        true_cvr = 0.05 + 0.1 * price_score + np.random.normal(0, 0.005)
        true_cvr = max(0.01, min(0.2, true_cvr))

        ad = Ad(text=f"Val {i}", channel="facebook", creative_type="text", price_score=price_score, trust_score=trust_score, urgency_score=urgency_score)
        res = sim.simulate_exposure(ad)

        results.append({
            'predicted_ctr': res['likes'] / num_agents,
            'actual_ctr': true_ctr,
            'predicted_cvr': res['conversions'] / max(1, res['likes']),
            'actual_cvr': true_cvr
        })

    df = pd.DataFrame(results)

    # Step 2.1: Split and Calibrate
    train_df, test_df = train_test_split(df, test_size=0.3, random_state=42)
    test_df = test_df.reset_index(drop=True) # Avoid reindexing issues

    calib = Calibrator(reference_n=10)
    calib.fit(train_df.to_dict('records'))

    # Save calibrator
    with open('models/calibrator.pkl', 'wb') as f:
        pickle.dump(calib, f)

    # Metrics before/after
    def get_metrics(data_actual, data_pred, suffix=""):
        mae = np.mean(np.abs(data_actual - data_pred))
        rmse = np.sqrt(np.mean((data_actual - data_pred)**2))
        corr, _ = pearsonr(data_actual, data_pred)
        return {f'MAE{suffix}': mae, f'RMSE{suffix}': rmse, f'Corr{suffix}': corr}

    before = get_metrics(test_df['actual_ctr'], test_df['predicted_ctr'], "_before")

    # Apply calibration
    calibrated_results = [calib.calibrate(row['predicted_ctr'], row['predicted_cvr']) for _, row in test_df.iterrows()]
    calibrated_ctr = [r[0] for r in calibrated_results]
    calibrated_cvr = [r[1] for r in calibrated_results]

    after = get_metrics(test_df['actual_ctr'], calibrated_ctr, "_after")

    print("\n--- Calibration Results (Test Set) ---")
    for k in before: print(f"{k}: {before[k]:.6f}")
    for k in after: print(f"{k}: {after[k]:.6f}")

    # Plot
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=test_df['actual_ctr'], y=test_df['predicted_ctr'], label='Raw', alpha=0.5)
    sns.scatterplot(x=test_df['actual_ctr'], y=calibrated_ctr, label='Calibrated', alpha=0.5)
    plt.title('Effect of Calibration on Prediction Accuracy')
    plt.savefig('outputs/synthetic_calibration.png')

    assert after['MAE_after'] < 0.05, f"MAE too high: {after['MAE_after']}"
    print("[SUCCESS] Calibration check passed: MAE < 0.05")

if __name__ == "__main__":
    synthetic_validation()
