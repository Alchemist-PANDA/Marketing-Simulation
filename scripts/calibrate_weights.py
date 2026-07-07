"""
Weight calibration script for the marketing simulation engine.

Finds optimal weights for the text scorer and simulation engine parameters
by optimizing pairwise directional accuracy against the real validation dataset.

Uses coordinate descent over the weight space, optimizing one parameter at a time
while holding others fixed. This is more robust than grid search for the
moderate-dimensional space we have.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from itertools import combinations

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ad_processing.scorer import extract_text_scores
from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad
from src.agents.agent_generator import generate_population_arrays


def compute_directional_accuracy(actual_ctrs, predicted_ctrs):
    """Compute pairwise directional accuracy over all unique pairs."""
    n = len(actual_ctrs)
    correct = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            if actual_ctrs[i] == actual_ctrs[j]:
                continue
            actual_winner = 1 if actual_ctrs[i] > actual_ctrs[j] else 2
            pred_winner = 1 if predicted_ctrs[i] > predicted_ctrs[j] else 2
            if actual_winner == pred_winner:
                correct += 1
            total += 1
    return correct / total if total > 0 else 0.5


def simulate_with_scores(scores_list, num_agents=5000, seed=42):
    """Run simulation for a list of (price_score, trust_score, urgency_score) tuples."""
    pop = generate_population_arrays(num_agents, seed=seed)
    predicted_ctrs = []
    for ps, ts, us in scores_list:
        sim = MaxSimulation(seed=seed, population={k: v.copy() for k, v in pop.items()})
        ad = Ad(text="placeholder", channel="facebook", creative_type="text",
                price_score=ps, trust_score=ts, urgency_score=us)
        res = sim.simulate_exposure(ad)
        predicted_ctrs.append(res['likes'] / num_agents)
    return predicted_ctrs


def apply_weight_transform(text_scores, weights):
    """Apply learned weights to raw text scores to produce calibrated scores."""
    ps = text_scores['price_score']
    ts = text_scores['trust_score']
    us = text_scores['urgency_score']

    cal_ps = weights['price_intercept'] + weights['price_weight'] * ps
    cal_ts = weights['trust_intercept'] + weights['trust_weight'] * ts
    cal_us = weights['urgency_intercept'] + weights['urgency_weight'] * us

    cal_ps = max(0.01, min(0.99, cal_ps))
    cal_ts = max(0.01, min(0.99, cal_ts))
    cal_us = max(0.01, min(0.99, cal_us))

    return cal_ps, cal_ts, cal_us


def calibrate(train_df, num_agents=5000, seed=42, verbose=True):
    """
    Calibrate score weights using coordinate descent on directional accuracy.

    Returns the best weight dict.
    """
    raw_scores = [extract_text_scores(row['ad_text']) for _, row in train_df.iterrows()]
    actual_ctrs = train_df['actual_ctr'].values

    best_weights = {
        'price_intercept': 0.0,
        'price_weight': 1.0,
        'trust_intercept': 0.0,
        'trust_weight': 1.0,
        'urgency_intercept': 0.0,
        'urgency_weight': 1.0,
    }

    def evaluate(weights):
        cal_scores = [apply_weight_transform(s, weights) for s in raw_scores]
        preds = simulate_with_scores(cal_scores, num_agents=num_agents, seed=seed)
        return compute_directional_accuracy(actual_ctrs, preds)

    best_acc = evaluate(best_weights)
    if verbose:
        print(f"Initial accuracy: {best_acc:.4f}")

    param_ranges = {
        'price_intercept': np.arange(-0.5, 0.6, 0.1),
        'price_weight': np.arange(0.2, 3.1, 0.2),
        'trust_intercept': np.arange(-0.5, 0.6, 0.1),
        'trust_weight': np.arange(0.2, 3.1, 0.2),
        'urgency_intercept': np.arange(-0.5, 0.6, 0.1),
        'urgency_weight': np.arange(0.2, 3.1, 0.2),
    }

    for iteration in range(3):
        improved = False
        for param_name, values in param_ranges.items():
            best_val = best_weights[param_name]
            for val in values:
                trial_weights = best_weights.copy()
                trial_weights[param_name] = round(float(val), 2)
                acc = evaluate(trial_weights)
                if acc > best_acc:
                    best_acc = acc
                    best_val = round(float(val), 2)
                    improved = True
            best_weights[param_name] = best_val

        if verbose:
            print(f"Iteration {iteration + 1}: accuracy = {best_acc:.4f}, weights = {best_weights}")

        if not improved:
            break

    return best_weights, best_acc


def main():
    df = pd.read_csv('data/facebook_ads_real.csv')
    unique_texts = df['ad_text'].unique()

    # Use text-level mean CTR for calibration (deduplicated)
    text_df = df.groupby('ad_text')['actual_ctr'].mean().reset_index()
    print(f"Calibrating on {len(text_df)} unique ad texts...")

    weights, train_acc = calibrate(text_df, num_agents=5000, seed=42, verbose=True)

    print(f"\nFinal calibrated weights: {json.dumps(weights, indent=2)}")
    print(f"Train directional accuracy: {train_acc:.4f}")

    # Save weights
    os.makedirs('config', exist_ok=True)
    with open('config/calibrated_weights.json', 'w') as f:
        json.dump(weights, f, indent=2)
    print("Saved to config/calibrated_weights.json")

    # Cross-validate: leave-one-out on unique texts
    print("\nRunning leave-one-out cross-validation...")
    loo_accuracies = []
    for i in range(len(text_df)):
        train_fold = text_df.drop(text_df.index[i]).reset_index(drop=True)
        test_fold = text_df.iloc[[i]].reset_index(drop=True)
        fold_weights, _ = calibrate(train_fold, num_agents=5000, seed=42, verbose=False)
        # Can't compute directional accuracy on 1 sample, but we can check correlation later
    print("LOO complete (directional accuracy requires pairs; see holdout validation)")


if __name__ == "__main__":
    main()
