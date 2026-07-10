"""
Train the CTR-prediction ensemble on the synthetic development benchmark.

Pipeline:
  1. Load (or generate) the synthetic dataset and its 70/15/15 split.
  2. Extract features (cached to models/ as .npy so reruns are fast).
  3. StandardScaler fit on TRAIN only.
  4. Train Ridge, HistGradientBoosting, RandomForest, MLP with light 5-fold
     CV tuning on TRAIN.
  5. Learn non-negative ensemble weights on VAL (maximize directional accuracy).
  6. Evaluate every model + the ensemble on the untouched HOLDOUT.
  7. Save models/ensemble_model.pkl and models/scaler.pkl and metrics JSON.

All randomness fixed with random_state=42.

⚠️  Accuracy here is measured on synthetic data — a software benchmark of the
pipeline, NOT a real-world performance claim. See src/ai/synth_data.py.
"""
from __future__ import annotations

import json
import os
import pickle
import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import GridSearchCV, KFold
from scipy.stats import pearsonr, spearmanr

from src.ai import synth_data
from src.ai.feature_extractor import build_features

SEED = 42
MODELS_DIR = "models"
DATA_DIR = "data"
np.random.seed(SEED)


# ── metrics ────────────────────────────────────────────────────────────────
def directional_accuracy(y_true, y_pred, n_pairs=40000, seed=SEED, margin=0.0):
    """Fraction of random ad *pairs* whose predicted order matches the truth.

    This is the metric that matters for A/B decisions: 'which ad is better?'.
    `margin` (relative) restricts to *decisive* pairs — where the two ads' true
    CTRs differ by at least `margin` (e.g. 0.10 = 10%). Real A/B tests only ask
    you to call a winner when a real winner exists; margin=0 counts every pair
    including near-ties.
    """
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    n = len(y_true)
    rng = np.random.default_rng(seed)
    i = rng.integers(0, n, size=n_pairs)
    j = rng.integers(0, n, size=n_pairs)
    if margin > 0:
        denom = np.maximum(np.abs(y_true[i]), np.abs(y_true[j]))
        mask = np.abs(y_true[i] - y_true[j]) >= margin * denom
    else:
        mask = y_true[i] != y_true[j]
    i, j = i[mask], j[mask]
    correct = np.sign(y_pred[i] - y_pred[j]) == np.sign(y_true[i] - y_true[j])
    return float(correct.mean())


def evaluate(y_true, y_pred):
    return {
        "directional_accuracy_all_pairs": round(directional_accuracy(y_true, y_pred), 4),
        "directional_accuracy_decisive": round(directional_accuracy(y_true, y_pred, margin=0.10), 4),
        "pearson": round(float(pearsonr(y_true, y_pred)[0]), 4),
        "spearman": round(float(spearmanr(y_true, y_pred)[0]), 4),
        "rmse": round(float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2))), 6),
    }


# ── data + features ─────────────────────────────────────────────────────────
def _load_split():
    paths = [f"{DATA_DIR}/synth_{s}.csv" for s in ("train", "val", "holdout")]
    if not all(os.path.exists(p) for p in paths):
        df = synth_data.generate()
        tr, val, hold = synth_data.split(df)
        os.makedirs(DATA_DIR, exist_ok=True)
        df.to_csv(f"{DATA_DIR}/expanded_real_dataset.csv", index=False)
        tr.to_csv(paths[0], index=False); val.to_csv(paths[1], index=False); hold.to_csv(paths[2], index=False)
        return tr, val, hold
    return (pd.read_csv(paths[0]), pd.read_csv(paths[1]), pd.read_csv(paths[2]))


def _features(df, tag):
    """Build features for a split, caching to models/feat_<tag>.npy."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    cache = f"{MODELS_DIR}/feat_{tag}.npy"
    if os.path.exists(cache):
        X = np.load(cache)
        if X.shape[0] == len(df):
            return X
    X = build_features(df["ad_text"].tolist())
    np.save(cache, X)
    return X


# ── training ─────────────────────────────────────────────────────────────────
def _train_models(Xtr, ytr):
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    models = {}

    print("  · Ridge …")
    ridge = GridSearchCV(Ridge(random_state=SEED),
                         {"alpha": [0.1, 1.0, 5.0, 10.0, 30.0]},
                         cv=kf, scoring="neg_root_mean_squared_error")
    ridge.fit(Xtr, ytr); models["ridge"] = ridge.best_estimator_

    print("  · HistGradientBoosting …")
    hgb = GridSearchCV(HistGradientBoostingRegressor(random_state=SEED),
                       {"max_depth": [3, 5, None], "learning_rate": [0.05, 0.1],
                        "max_iter": [300], "l2_regularization": [0.0, 1.0]},
                       cv=kf, scoring="neg_root_mean_squared_error")
    hgb.fit(Xtr, ytr); models["hist_gbr"] = hgb.best_estimator_

    # NOTE: A RandomForest was evaluated but pickled to ~49 MB (300 deep trees
    # over 401 features) for only a ~0.6pp gain over Ridge — too heavy to ship in
    # the repo for Streamlit Cloud. HistGradientBoosting gives comparable
    # non-linear power at a fraction of the size, so RF is intentionally omitted.
    print("  · MLP …")
    mlp = GridSearchCV(MLPRegressor(random_state=SEED, max_iter=800, early_stopping=True),
                       {"hidden_layer_sizes": [(128, 64), (256, 128)],
                        "alpha": [1e-4, 1e-3]},
                       cv=3, scoring="neg_root_mean_squared_error")
    mlp.fit(Xtr, ytr); models["mlp"] = mlp.best_estimator_
    return models


def _learn_weights(models, Xval, yval):
    """Non-negative weights over model predictions, tuned on VAL for directional
    accuracy via a light random search on the simplex."""
    preds = {k: m.predict(Xval) for k, m in models.items()}
    names = list(models.keys())
    P = np.vstack([preds[k] for k in names])  # (n_models, n_val)
    rng = np.random.default_rng(SEED)
    best_w, best_da = None, -1.0
    # include each single model + Dirichlet random mixes
    candidates = list(np.eye(len(names)))
    candidates += [rng.dirichlet(np.ones(len(names))) for _ in range(4000)]
    for w in candidates:
        da = directional_accuracy(yval, w @ P)
        if da > best_da:
            best_da, best_w = da, np.asarray(w)
    return dict(zip(names, best_w.tolist())), best_da


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("Loading data …")
    tr, val, hold = _load_split()
    print(f"  train={len(tr)}  val={len(val)}  holdout={len(hold)}")

    print("Extracting features (cached) …")
    Xtr_raw, Xval_raw, Xho_raw = _features(tr, "train"), _features(val, "val"), _features(hold, "holdout")
    ytr, yval, yho = tr["actual_ctr"].values, val["actual_ctr"].values, hold["actual_ctr"].values

    scaler = StandardScaler().fit(Xtr_raw)
    Xtr, Xval, Xho = scaler.transform(Xtr_raw), scaler.transform(Xval_raw), scaler.transform(Xho_raw)

    # Train on CTR in percentage points (×100). CTR values are ~0.01, which is
    # numerically awkward for the MLP; scaling up stabilizes optimization. All
    # predictions are divided back to raw CTR before evaluation.
    Y_SCALE = 100.0
    print("Training models …")
    models = _train_models(Xtr, ytr * Y_SCALE)

    print("Learning ensemble weights on validation …")
    # weights learned in scaled space; directional accuracy is scale-invariant
    weights, val_da = _learn_weights(models, Xval, yval * Y_SCALE)
    print(f"  weights = { {k: round(v,3) for k,v in weights.items()} }  (val DA={val_da:.4f})")

    # ── evaluate everything on the untouched holdout (back in raw CTR units) ──
    def ens_pred(X):
        return sum(w * models[k].predict(X) for k, w in weights.items()) / Y_SCALE

    results = {"per_model_holdout": {}, "ensemble_holdout": {}, "ensemble_validation": {}}
    for k, m in models.items():
        results["per_model_holdout"][k] = evaluate(yho, m.predict(Xho) / Y_SCALE)
    results["ensemble_holdout"] = evaluate(yho, ens_pred(Xho))
    results["ensemble_validation"] = evaluate(yval, ens_pred(Xval))

    # ── persist ──
    scaler_path = f"{MODELS_DIR}/scaler.pkl"
    ens_path = f"{MODELS_DIR}/ensemble_model.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    with open(ens_path, "wb") as f:
        pickle.dump({
            "models": models,
            "weights": weights,
            "scaler": scaler,
            "y_scale": Y_SCALE,
            "model_version": "ensemble-v1-synth",
            "feature_layout": "stats(17)+minilm(384)",
            "data_provenance": "SYNTHETIC development benchmark (src/ai/synth_data.py); "
                               "not a real-world performance claim.",
            "metrics": results,
        }, f)

    with open(f"{MODELS_DIR}/ensemble_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== HOLDOUT RESULTS (synthetic benchmark) ===")
    print(f"  {'model':16s} {'DA(all)':>8s} {'DA(dec.)':>9s} {'pearson':>8s} {'rmse':>8s}")
    for k, v in results["per_model_holdout"].items():
        print(f"  {k:16s} {v['directional_accuracy_all_pairs']:8.4f} "
              f"{v['directional_accuracy_decisive']:9.4f} {v['pearson']:8.3f} {v['rmse']:8.5f}")
    e = results["ensemble_holdout"]
    print(f"  {'ENSEMBLE':16s} {e['directional_accuracy_all_pairs']:8.4f} "
          f"{e['directional_accuracy_decisive']:9.4f} {e['pearson']:8.3f} {e['rmse']:8.5f}  "
          f"(spearman={e['spearman']:.3f})")
    print(f"\nSaved: {ens_path}, {scaler_path}, {MODELS_DIR}/ensemble_metrics.json")
    return results


if __name__ == "__main__":
    main()
