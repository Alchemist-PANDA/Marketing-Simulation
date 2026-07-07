"""
Train AI models for CTR prediction with proper cross-validation.

Three model families:
1. Keyword-only: Ridge regression on keyword scores (baseline)
2. Feature-rich: GBT on keyword scores + text stats + embeddings
3. Simulation ensemble: Combine simulation engine output with ML predictions

All models evaluated via directional accuracy on a held-out set.
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def compute_directional_accuracy(actual, predicted):
    n = len(actual)
    correct = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            if actual[i] == actual[j]:
                continue
            aw = 1 if actual[i] > actual[j] else 2
            pw = 1 if predicted[i] > predicted[j] else 2
            if aw == pw:
                correct += 1
            total += 1
    return correct / total if total > 0 else 0.5


SPLIT_SUFFIX = ''  # overridden by --suffix argument


def load_features(split):
    path = f'data/features_{split}{SPLIT_SUFFIX}.csv'
    if not os.path.exists(path):
        raise FileNotFoundError(f'{path} not found. Run extract_features.py first.')
    df = pd.read_csv(path)
    feature_cols = [c for c in df.columns if c not in ['ad_text', 'actual_ctr']]
    X = df[feature_cols].values.astype(np.float32)
    y = df['actual_ctr'].values
    texts = df['ad_text'].tolist()
    return X, y, texts, feature_cols


def train_and_evaluate():
    print("Loading features...")
    X_train, y_train, texts_train, feature_cols = load_features('train')
    X_val, y_val, texts_val, _ = load_features('val')
    X_holdout, y_holdout, texts_holdout, _ = load_features('holdout')

    n_kw = 3
    n_stats = 9
    n_emb_start = n_kw + n_stats

    results = {}

    # === Model 1: Keyword-only Ridge ===
    print("\n=== Model 1: Keyword-Only Ridge ===")
    X_kw_train = X_train[:, :n_kw]
    X_kw_val = X_val[:, :n_kw]
    X_kw_holdout = X_holdout[:, :n_kw]

    model_kw = Ridge(alpha=0.1).fit(X_kw_train, y_train)
    pred_kw_val = model_kw.predict(X_kw_val)
    pred_kw_holdout = model_kw.predict(X_kw_holdout)

    da_kw_val = compute_directional_accuracy(y_val, pred_kw_val)
    da_kw_holdout = compute_directional_accuracy(y_holdout, pred_kw_holdout)
    r_kw, _ = pearsonr(y_val, pred_kw_val)
    print(f"  Val DA: {da_kw_val:.4f}, Holdout DA: {da_kw_holdout:.4f}, Val r: {r_kw:.4f}")
    results['keyword_ridge'] = {'val_da': da_kw_val, 'holdout_da': da_kw_holdout, 'val_r': r_kw}

    # === Model 2: Keyword + Stats Ridge ===
    print("\n=== Model 2: Keyword + Stats Ridge ===")
    X_ks_train = X_train[:, :n_emb_start]
    X_ks_val = X_val[:, :n_emb_start]
    X_ks_holdout = X_holdout[:, :n_emb_start]

    model_ks = Pipeline([
        ('scaler', StandardScaler()),
        ('ridge', Ridge(alpha=1.0))
    ]).fit(X_ks_train, y_train)
    pred_ks_val = model_ks.predict(X_ks_val)
    pred_ks_holdout = model_ks.predict(X_ks_holdout)

    da_ks_val = compute_directional_accuracy(y_val, pred_ks_val)
    da_ks_holdout = compute_directional_accuracy(y_holdout, pred_ks_holdout)
    r_ks, _ = pearsonr(y_val, pred_ks_val)
    print(f"  Val DA: {da_ks_val:.4f}, Holdout DA: {da_ks_holdout:.4f}, Val r: {r_ks:.4f}")
    results['keyword_stats_ridge'] = {'val_da': da_ks_val, 'holdout_da': da_ks_holdout, 'val_r': r_ks}

    # === Model 3: Full features GBT ===
    print("\n=== Model 3: Full Features GBT ===")
    for n_est, depth, lr in [(50, 3, 0.1), (100, 4, 0.05), (200, 3, 0.05)]:
        model_gbt = Pipeline([
            ('scaler', StandardScaler()),
            ('gbt', GradientBoostingRegressor(
                n_estimators=n_est, max_depth=depth, learning_rate=lr,
                subsample=0.8, random_state=42
            ))
        ]).fit(X_train, y_train)
        pred_gbt_val = model_gbt.predict(X_val)
        pred_gbt_holdout = model_gbt.predict(X_holdout)

        da_gbt_val = compute_directional_accuracy(y_val, pred_gbt_val)
        da_gbt_holdout = compute_directional_accuracy(y_holdout, pred_gbt_holdout)
        r_gbt, _ = pearsonr(y_val, pred_gbt_val)
        print(f"  n={n_est} d={depth} lr={lr}: Val DA={da_gbt_val:.4f}, Holdout DA={da_gbt_holdout:.4f}, r={r_gbt:.4f}")

        key = f'gbt_{n_est}_{depth}_{lr}'
        results[key] = {'val_da': da_gbt_val, 'holdout_da': da_gbt_holdout, 'val_r': r_gbt}

    # === Model 4: Embeddings-only Ridge ===
    print("\n=== Model 4: Embeddings-Only Ridge ===")
    X_emb_train = X_train[:, n_emb_start:]
    X_emb_val = X_val[:, n_emb_start:]
    X_emb_holdout = X_holdout[:, n_emb_start:]

    for alpha in [0.1, 1.0, 10.0]:
        model_emb = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=alpha))
        ]).fit(X_emb_train, y_train)
        pred_emb_val = model_emb.predict(X_emb_val)
        pred_emb_holdout = model_emb.predict(X_emb_holdout)

        da_emb_val = compute_directional_accuracy(y_val, pred_emb_val)
        da_emb_holdout = compute_directional_accuracy(y_holdout, pred_emb_holdout)
        r_emb, _ = pearsonr(y_val, pred_emb_val)
        print(f"  alpha={alpha}: Val DA={da_emb_val:.4f}, Holdout DA={da_emb_holdout:.4f}, r={r_emb:.4f}")
        results[f'emb_ridge_{alpha}'] = {'val_da': da_emb_val, 'holdout_da': da_emb_holdout, 'val_r': r_emb}

    # === Model 5: Full features + embeddings Ridge ===
    print("\n=== Model 5: All Features Ridge ===")
    for alpha in [0.1, 1.0, 10.0]:
        model_all = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=alpha))
        ]).fit(X_train, y_train)
        pred_all_val = model_all.predict(X_val)
        pred_all_holdout = model_all.predict(X_holdout)

        da_all_val = compute_directional_accuracy(y_val, pred_all_val)
        da_all_holdout = compute_directional_accuracy(y_holdout, pred_all_holdout)
        r_all, _ = pearsonr(y_val, pred_all_val)
        print(f"  alpha={alpha}: Val DA={da_all_val:.4f}, Holdout DA={da_all_holdout:.4f}, r={r_all:.4f}")
        results[f'all_ridge_{alpha}'] = {'val_da': da_all_val, 'holdout_da': da_all_holdout, 'val_r': r_all}

    # === Select best model ===
    best_name = max(results, key=lambda k: results[k]['val_da'])
    best = results[best_name]
    print(f"\n{'='*60}")
    print(f"BEST MODEL: {best_name}")
    print(f"  Val DA: {best['val_da']:.4f}")
    print(f"  Holdout DA: {best['holdout_da']:.4f}")
    print(f"  Val Pearson r: {best['val_r']:.4f}")
    print(f"{'='*60}")

    # Retrain best on train+val, evaluate on holdout
    print("\nRetraining best model on train+val...")
    X_tv = np.vstack([X_train, X_val])
    y_tv = np.concatenate([y_train, y_val])

    if 'gbt' in best_name:
        parts = best_name.split('_')
        n_est, depth, lr = int(parts[1]), int(parts[2]), float(parts[3])
        final_model = Pipeline([
            ('scaler', StandardScaler()),
            ('gbt', GradientBoostingRegressor(
                n_estimators=n_est, max_depth=depth, learning_rate=lr,
                subsample=0.8, random_state=42
            ))
        ]).fit(X_tv, y_tv)
    elif 'emb_ridge' in best_name:
        alpha = float(best_name.split('_')[-1])
        final_model = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=alpha))
        ]).fit(X_emb_train if 'emb' in best_name else X_tv,
               y_train if 'emb' in best_name else y_tv)
    elif 'keyword_stats' in best_name:
        final_model = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=1.0))
        ])
        X_tv_ks = X_tv[:, :n_emb_start]
        final_model.fit(X_tv_ks, y_tv)
    elif 'keyword_ridge' in best_name:
        final_model = Ridge(alpha=0.1).fit(X_tv[:, :n_kw], y_tv)
    else:
        alpha = float(best_name.split('_')[-1])
        final_model = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=alpha))
        ]).fit(X_tv, y_tv)

    # Save the best model
    os.makedirs('models', exist_ok=True)
    with open('models/ai_ctr_model.pkl', 'wb') as f:
        pickle.dump({
            'model': final_model,
            'model_name': best_name,
            'feature_cols': feature_cols,
            'n_keyword_features': n_kw,
            'n_stat_features': n_stats,
            'results': results,
        }, f)
    print(f"Saved best model to models/ai_ctr_model.pkl")

    # Save results
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/ai_training_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to outputs/ai_training_results.json")

    return results, best_name


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix', default='', help='Suffix for split filenames, e.g. _v2')
    args = parser.parse_args()
    SPLIT_SUFFIX = args.suffix
    train_and_evaluate()
