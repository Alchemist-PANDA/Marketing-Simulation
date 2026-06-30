import os
import sys
import json
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from scipy.optimize import minimize
from scipy.stats import pearsonr
from sentence_transformers import SentenceTransformer
from sklearn.metrics import mean_absolute_error
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ad_processing.ad import Ad

def get_directional_accuracy(actuals, preds, n_pairs=1000):
    correct = 0
    total = 0
    np.random.seed(42)
    n = len(actuals)
    if n < 2: return 0.0
    for _ in range(n_pairs):
        i, j = np.random.choice(n, 2, replace=False)
        actual_diff = actuals[i] - actuals[j]
        pred_diff = preds[i] - preds[j]
        if (actual_diff > 0 and pred_diff > 0) or (actual_diff < 0 and pred_diff < 0):
            correct += 1
        total += 1
    return correct / total if total > 0 else 0.0

def run_embedding_sim(weights, ads):
    bias = weights[-1]
    scale = weights[-2]
    # Rest of weights are for the embedding (384 for MiniLM)
    emb_weights = weights[:-2]

    preds = []
    for ad in ads:
        utility = np.dot(ad.embedding, emb_weights) + bias
        prob = 1.0 / (1.0 + np.exp(-utility / scale))
        preds.append(prob)
    return np.array(preds)

def objective(weights, ads, actual_ctrs):
    preds = run_embedding_sim(weights, ads)
    if np.std(preds) == 0: return 1.0
    corr, _ = pearsonr(actual_ctrs, preds)
    mae = np.mean(np.abs(actual_ctrs - preds))
    return (1.0 - corr) + 10.0 * mae

def main():
    print("Starting Embedding-based Agent Calibration and Hold-Out Validation...")

    # 1. Load data and split
    df = pd.read_csv('data/real_ctr.csv')
    train_df, temp_df = train_test_split(df, test_size=0.3, random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

    calib_df = pd.concat([train_df, val_df])

    # 2. Extract embeddings
    print("Pre-calculating embeddings for calibration set...")
    calib_ads = [Ad(text=row['ad_text'], channel='facebook', creative_type='text') for _, row in calib_df.iterrows()]
    calib_actuals = calib_df['actual_ctr'].values

    # 3. Optimize 384 + 2 weights
    print("\n--- Calibrating Embedding Weights (Train+Val Set) ---")
    # Initial weights: bias -4, scale 1, others 0
    initial_weights = np.zeros(386)
    initial_weights[-1] = -4.0
    initial_weights[-2] = 1.0

    res = minimize(
        objective,
        initial_weights,
        args=(calib_ads, calib_actuals),
        method='L-BFGS-B', # Faster for high-dimensional
        options={'maxiter': 100, 'disp': True}
    )

    opt_weights = res.x

    # 4. Evaluate on Test set
    print("\n--- Evaluating Embedding Agent (Test Set) ---")
    test_ads = [Ad(text=row['ad_text'], channel='facebook', creative_type='text') for _, row in test_df.iterrows()]
    y_test = test_df['actual_ctr'].values

    preds = run_embedding_sim(opt_weights, test_ads)
    corr, _ = pearsonr(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    dir_acc = get_directional_accuracy(y_test, preds)

    print(f"Pearson Correlation: {corr:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.6f}")
    print(f"Directional Accuracy: {dir_acc:.2%}")

    # 5. Save results
    os.makedirs('config', exist_ok=True)
    with open('config/embedding_weights.json', 'w') as f:
        json.dump(opt_weights.tolist(), f)

    success = corr > 0.7 and mae < 0.03

    report = f"""# 🏆 Embedding-based Agent Holdout Validation Report

## 🧪 Model: EmbeddingAgent (Direct use of 384-d embeddings)
- **Pearson Correlation**: {corr:.4f}
- **Mean Absolute Error (MAE)**: {mae:.6f}
- **Directional Accuracy**: {dir_acc:.2%}

## ⚖️ Final Verdict
"""
    if success:
        report += "**9/10 achieved – embedding-based linear simulation generalises to unseen data.**\n"
    else:
        report += "**9/10 not yet achieved.**\n"

    with open('EMBEDDING_VALIDATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)

    if success:
        print("\n9/10 achieved.")
    else:
        print("\n9/10 not yet achieved.")

if __name__ == '__main__':
    main()
