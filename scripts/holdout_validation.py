"""
Holdout validation of directional accuracy.

Computes pairwise directional accuracy (concordance) between simulation-predicted
CTR and actual CTR on the real ad dataset. Reports:
- All-pairs accuracy on deduplicated texts (most rigorous)
- Random-pairs accuracy on full dataset (matches original methodology)
- Pearson and Spearman correlation
- Bootstrap confidence intervals
- Per-ad predictions for inspection

No calibration weights are fit to this data — the simulation engine's
psychographic model and the text scorer's keyword rules are the only
components driving predictions. This is a zero-shot evaluation.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad
from src.agents.agent_generator import generate_population_arrays


def run_validation(num_agents=10000, seed=42, data_path='data/facebook_ads_real.csv'):
    df = pd.read_csv(data_path)
    print(f"Validating on {len(df)} rows ({df['ad_text'].nunique()} unique texts)")
    print(f"Using {num_agents} agents per simulation, seed={seed}")

    pop = generate_population_arrays(num_agents, seed=seed)

    predicted_ctrs = []
    ad_scores = []
    for _, row in df.iterrows():
        sim = MaxSimulation(seed=seed, population={k: v.copy() for k, v in pop.items()})
        ad = Ad(text=row['ad_text'], channel='facebook', creative_type='text')
        res = sim.simulate_exposure(ad)
        predicted_ctrs.append(res['likes'] / num_agents)
        ad_scores.append({
            'price_score': ad.price_score,
            'trust_score': ad.trust_score,
            'urgency_score': ad.urgency_score,
        })

    df['predicted_ctr'] = predicted_ctrs
    for k in ['price_score', 'trust_score', 'urgency_score']:
        df[k] = [s[k] for s in ad_scores]

    text_df = df.groupby('ad_text').agg({
        'actual_ctr': 'mean',
        'predicted_ctr': 'first',
        'price_score': 'first',
        'trust_score': 'first',
        'urgency_score': 'first',
    }).reset_index()

    # 1. All-pairs on unique texts
    n = len(text_df)
    correct_all = 0
    total_all = 0
    for i in range(n):
        for j in range(i + 1, n):
            if text_df.iloc[i]['actual_ctr'] == text_df.iloc[j]['actual_ctr']:
                continue
            aw = 1 if text_df.iloc[i]['actual_ctr'] > text_df.iloc[j]['actual_ctr'] else 2
            pw = 1 if text_df.iloc[i]['predicted_ctr'] > text_df.iloc[j]['predicted_ctr'] else 2
            if aw == pw:
                correct_all += 1
            total_all += 1

    all_pairs_da = correct_all / total_all if total_all > 0 else 0

    # 2. Random pairs (original methodology)
    np.random.seed(42)
    correct_rand = 0
    total_rand = 1000
    for _ in range(total_rand):
        i, j = np.random.choice(len(df), 2, replace=False)
        aw = 1 if df.iloc[i]['actual_ctr'] > df.iloc[j]['actual_ctr'] else 2
        pw = 1 if df.iloc[i]['predicted_ctr'] > df.iloc[j]['predicted_ctr'] else 2
        if aw == pw:
            correct_rand += 1
    rand_da = correct_rand / total_rand

    # 3. Correlation
    corr, pval = pearsonr(text_df['actual_ctr'], text_df['predicted_ctr'])
    sr, sp = spearmanr(text_df['actual_ctr'], text_df['predicted_ctr'])

    # 4. Bootstrap confidence interval for all-pairs DA
    bootstrap_das = []
    for _ in range(200):
        idx = np.random.choice(n, n, replace=True)
        boot_actual = text_df.iloc[idx]['actual_ctr'].values
        boot_pred = text_df.iloc[idx]['predicted_ctr'].values
        bc = 0
        bt = 0
        for i in range(n):
            for j in range(i + 1, n):
                if boot_actual[i] == boot_actual[j]:
                    continue
                aw = 1 if boot_actual[i] > boot_actual[j] else 2
                pw = 1 if boot_pred[i] > boot_pred[j] else 2
                if aw == pw:
                    bc += 1
                bt += 1
        if bt > 0:
            bootstrap_das.append(bc / bt)

    ci_low = np.percentile(bootstrap_das, 2.5)
    ci_high = np.percentile(bootstrap_das, 97.5)

    # MAE
    mae = np.mean(np.abs(text_df['actual_ctr'] - text_df['predicted_ctr']))

    # Report
    print(f"\n{'='*60}")
    print(f"HOLDOUT VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"All-pairs directional accuracy:  {all_pairs_da:.4f} ({correct_all}/{total_all} pairs)")
    print(f"Random-pairs directional accuracy: {rand_da:.4f} ({correct_rand}/{total_rand} pairs)")
    print(f"95% bootstrap CI:                [{ci_low:.4f}, {ci_high:.4f}]")
    print(f"Pearson correlation:             {corr:.4f} (p={pval:.4g})")
    print(f"Spearman rank correlation:       {sr:.4f}")
    print(f"Mean Absolute Error:             {mae:.6f}")
    print(f"Actual CTR range:                [{text_df['actual_ctr'].min():.4f}, {text_df['actual_ctr'].max():.4f}]")
    print(f"Predicted CTR range:             [{text_df['predicted_ctr'].min():.4f}, {text_df['predicted_ctr'].max():.4f}]")
    print(f"{'='*60}")

    # Per-ad breakdown
    print(f"\nPer-Ad Predictions (sorted by actual CTR):")
    print(f"{'Actual':>8} {'Pred':>8} {'P':>5} {'T':>5} {'U':>5} | Ad Text")
    print(f"{'-'*8} {'-'*8} {'-'*5} {'-'*5} {'-'*5} | {'-'*50}")
    for _, row in text_df.sort_values('actual_ctr').iterrows():
        print(f"{row['actual_ctr']:8.4f} {row['predicted_ctr']:8.4f} "
              f"{row['price_score']:5.2f} {row['trust_score']:5.2f} {row['urgency_score']:5.2f} "
              f"| {row['ad_text'][:50]}")

    # Save results
    os.makedirs('outputs', exist_ok=True)
    results = {
        'all_pairs_directional_accuracy': round(all_pairs_da, 4),
        'random_pairs_directional_accuracy': round(rand_da, 4),
        'bootstrap_ci_95': [round(ci_low, 4), round(ci_high, 4)],
        'pearson_r': round(corr, 4),
        'spearman_rho': round(sr, 4),
        'mae': round(mae, 6),
        'num_unique_texts': n,
        'num_agents': num_agents,
        'seed': seed,
    }
    with open('outputs/holdout_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to outputs/holdout_validation_results.json")

    return results


if __name__ == "__main__":
    run_validation()
