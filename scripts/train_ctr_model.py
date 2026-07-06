"""
Train a CTR prediction model using sentence embeddings from real ad text.

This model learns the mapping from ad text embeddings to CTR directly,
bypassing the intermediate price/trust/urgency scoring layer. It serves
as a calibration/ensemble layer on top of the simulation engine.
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def train_ctr_model():
    from sentence_transformers import SentenceTransformer

    df = pd.read_csv('data/facebook_ads_real.csv')
    text_df = df.groupby('ad_text')['actual_ctr'].mean().reset_index()

    print(f"Training on {len(text_df)} unique ad texts...")

    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    texts = text_df['ad_text'].tolist()
    embeddings = embedder.encode(texts)

    y = text_df['actual_ctr'].values

    # LOO cross-validation to find best alpha
    loo = LeaveOneOut()
    best_alpha = 0.1
    best_da = 0

    for alpha in [0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]:
        y_pred = cross_val_predict(Ridge(alpha=alpha), embeddings, y, cv=loo)
        n = len(y)
        correct = sum(1 for i in range(n) for j in range(i + 1, n)
                      if y[i] != y[j] and ((y[i] > y[j]) == (y_pred[i] > y_pred[j])))
        total = sum(1 for i in range(n) for j in range(i + 1, n) if y[i] != y[j])
        da = correct / total
        corr, _ = pearsonr(y, y_pred)
        print(f"  alpha={alpha:<5}: DA={da:.4f} r={corr:.4f}")
        if da > best_da:
            best_da = da
            best_alpha = alpha

    print(f"\nBest alpha: {best_alpha} (DA={best_da:.4f})")

    # Train final model
    model = Ridge(alpha=best_alpha).fit(embeddings, y)

    # Save
    os.makedirs('models', exist_ok=True)
    with open('models/ctr_embedding_model.pkl', 'wb') as f:
        pickle.dump({'model': model, 'alpha': best_alpha}, f)
    print("Saved models/ctr_embedding_model.pkl")

    # Also retrain the score prediction models on real data
    # Use the text scorer's keyword-derived scores as "ground truth"
    # since we don't have human-labeled scores for these real texts
    from src.ad_processing.scorer import extract_text_scores

    score_data = [extract_text_scores(t) for t in texts]
    for target in ['price_score', 'trust_score', 'urgency_score']:
        y_score = np.array([s[target] for s in score_data])
        if np.std(y_score) < 0.01:
            print(f"  Skipping {target} (no variance)")
            continue
        model_score = Ridge(alpha=0.5).fit(embeddings, y_score)
        fname = f"models/{target.replace('_score', '')}_scorer.pkl"
        with open(fname, 'wb') as f:
            pickle.dump(model_score, f)
        print(f"  Retrained {fname}")

    return best_da


if __name__ == "__main__":
    train_ctr_model()
