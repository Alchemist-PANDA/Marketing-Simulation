"""
Ecommerce-specialized ranker: same deployable-mode protocol as train_ranker_v5.py
(no objective/industry features, averaged-both-orderings evaluation, isotonic
calibration + confidence gating) but trained EXCLUSIVELY on ecommerce ads/pairs
so the model's weights aren't diluted by Insurance/Gaming/Travel/Social copy
patterns that ecommerce businesses don't care about.
"""

import csv
import json
import sys
import numpy as np

sys.path.insert(0, "/home/user/Marketing-Simulation")

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.isotonic import IsotonicRegression
import joblib

from src.ai.creative_ranker import (
    engineered_features, visual_vector, FEATURE_NAMES, VISUAL_KEYS,
    ProbaEnsemble,
)

ADS_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_ads_clean.csv"
PAIRS_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_validation_pairs.csv"
VF_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_visual_features.csv"
MODEL_PATH = "/home/user/Marketing-Simulation/models/creative_ranker_ecom_candidate.joblib"
EVAL_PATH = "/home/user/Marketing-Simulation/validation_data/ranker_eval_ecom.json"

N_PCA = 64
rng = np.random.RandomState(42)

with open(ADS_PATH, encoding="utf-8") as f:
    ads = {r["id"]: r for r in csv.DictReader(f)}
with open(PAIRS_PATH, encoding="utf-8") as f:
    pairs = list(csv.DictReader(f))
vf = {}
try:
    with open(VF_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            vf[r["id"]] = {k: float(r[k]) for k in VISUAL_KEYS}
except FileNotFoundError:
    pass
print(f"Ecommerce ads: {len(ads)}, pairs: {len(pairs)}, visual features: {len(vf)}")

print("Computing embeddings (MiniLM)...")
from sentence_transformers import SentenceTransformer
st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
ad_ids = list(ads.keys())
texts = [ads[i]["ad_title"] for i in ad_ids]
raw_emb = st_model.encode(texts, batch_size=128, show_progress_bar=False,
                          normalize_embeddings=True)

train_mask = np.array([ads[i]["split"] == "train" for i in ad_ids])
pca = PCA(n_components=N_PCA, random_state=42).fit(raw_emb[train_mask])
emb = pca.transform(raw_emb).astype(np.float32)
print(f"PCA-{N_PCA} explains {pca.explained_variance_ratio_.sum()*100:.1f}%")

train_vf = [vf[i] for i in ad_ids
            if ads[i]["split"] == "train" and i in vf]
visual_mean = np.array(
    [np.mean([d[k] for d in train_vf]) for k in VISUAL_KEYS],
    dtype=np.float32) if train_vf else None
print(f"visual_mean (train, n={len(train_vf)}): {visual_mean}")

_fake_art = {"visual_mean": visual_mean}


def ad_visual(aid):
    return visual_vector(vf.get(aid), _fake_art)


feat = {}
for k, aid in enumerate(ad_ids):
    a = ads[aid]
    feat[aid] = np.concatenate([
        emb[k],
        engineered_features(a["ad_title"]),
        np.array([np.log1p(max(0.0, float(a["video_duration"] or 0)))],
                 dtype=np.float32),
        ad_visual(aid),
    ]).astype(np.float32)
DIM = len(next(iter(feat.values())))
print(f"Feature dim: {DIM}")

train_feats = np.stack([feat[i] for i in ad_ids if ads[i]["split"] == "train"])
mean_feat = train_feats.mean(axis=0).astype(np.float32)

split_pairs = {"train": [], "val": [], "holdout": []}
for p in pairs:
    split_pairs[p["split"]].append(p)
for k, v in split_pairs.items():
    dec = sum(1 for p in v if p["is_decisive"] == "True")
    sb = sum(1 for p in v if p["pair_type"] == "same_brand")
    print(f"{k}: {len(v)} ({dec} decisive, {sb} same-brand)")


def pair_x(fa, fb):
    d = fa - fb
    return np.concatenate([d, np.abs(d)])


def make_matrices(plist):
    Xf, Xr, meta = [], [], []
    for p in plist:
        fa, fb = feat[p["ad_a_id"]], feat[p["ad_b_id"]]
        Xf.append(pair_x(fa, fb))
        Xr.append(pair_x(fb, fa))
        meta.append(p)
    return (np.array(Xf, dtype=np.float32),
            np.array(Xr, dtype=np.float32), meta)


X_tr_f, X_tr_r, _ = make_matrices(split_pairs["train"])
X_tr = np.concatenate([X_tr_f, X_tr_r])
y_tr = np.concatenate([np.ones(len(X_tr_f)), np.zeros(len(X_tr_r))])
X_va_f, X_va_r, meta_va = make_matrices(split_pairs["val"])
X_ho_f, X_ho_r, meta_ho = make_matrices(split_pairs["holdout"])

scaler = StandardScaler().fit(X_tr)
X_tr_s = scaler.transform(X_tr)

candidates = {
    "logreg_C0.1": LogisticRegression(C=0.1, max_iter=3000),
    "logreg_C0.03": LogisticRegression(C=0.03, max_iter=3000),
    "hgb": HistGradientBoostingClassifier(
        max_iter=800, learning_rate=0.04, max_leaf_nodes=31,
        l2_regularization=1.0, random_state=42),
    "hgb_deep": HistGradientBoostingClassifier(
        max_iter=500, learning_rate=0.06, max_depth=7,
        l2_regularization=0.5, random_state=7),
}
for name, m in candidates.items():
    m.fit(X_tr_s, y_tr)
ens = ProbaEnsemble(list(candidates.values()))


def avg_prob(model, Xf, Xr):
    pf = model.predict_proba(scaler.transform(Xf))[:, 1]
    pr = model.predict_proba(scaler.transform(Xr))[:, 1]
    return (pf + (1.0 - pr)) / 2.0


val_scores = {}
for name, m in list(candidates.items()) + [("ensemble", ens)]:
    p = avg_prob(m, X_va_f, X_va_r)
    val_scores[name] = float((p >= 0.5).mean())
    print(f"val accuracy {name}: {val_scores[name]*100:.1f}%")

best_name = max(val_scores, key=val_scores.get)
model = ens if best_name == "ensemble" else candidates[best_name]
print(f"Selected: {best_name}")

p_va = avg_prob(model, X_va_f, X_va_r)
p_va_sym = np.concatenate([p_va, 1.0 - p_va])
y_va_sym = np.concatenate([np.ones(len(p_va)), np.zeros(len(p_va))])
iso = IsotonicRegression(out_of_bounds="clip").fit(p_va_sym, y_va_sym)


def evaluate(Xf, Xr, meta, threshold):
    p = iso.predict(avg_prob(model, Xf, Xr))
    conf = np.maximum(p, 1 - p)
    called = conf >= threshold
    pred = (p >= 0.5).astype(int)
    y = np.ones(len(p), dtype=int)
    dec = np.array([m["is_decisive"] == "True" for m in meta])
    sb = np.array([m["pair_type"] == "same_brand" for m in meta])
    gaps = np.array([float(m["ctr_gap"]) for m in meta])
    dc = dec & called

    def acc(mask):
        return float((pred[mask] == y[mask]).mean()) if mask.any() else None

    out = {
        "n": int(len(y)),
        "overall_acc": acc(np.ones(len(y), bool)),
        "same_brand_acc": acc(sb), "same_brand_n": int(sb.sum()),
        "decisive_acc": acc(dec),
        "called_frac": float(called.mean()), "called_n": int(called.sum()),
        "called_acc": acc(called),
        "decisive_called_acc": acc(dc), "decisive_called_n": int(dc.sum()),
        "same_brand_called_acc": acc(sb & called),
        "same_brand_called_n": int((sb & called).sum()),
    }
    for lo, hi, label in [(0, .05, "<5pp"), (.05, .10, "5-10pp"),
                          (.10, .20, "10-20pp"), (.20, .30, "20-30pp"),
                          (.30, 9, "30pp+")]:
        m_ = (gaps >= lo) & (gaps < hi)
        if m_.any():
            out[f"gap_{label}"] = {"n": int(m_.sum()), "acc": acc(m_)}
    return out


# sweep threshold on VAL, target >=75% called acc with the best call rate we
# can get (not just the first threshold that clears 75% val — that overfits
# the threshold to val noise). Track all thresholds clearing 75%, prefer the
# lowest such threshold (highest call rate) for a more useful product.
best_t, best_ev = 0.50, evaluate(X_va_f, X_va_r, meta_va, 0.50)
qualifying = []
for t in np.arange(0.50, 0.97, 0.01):
    ev = evaluate(X_va_f, X_va_r, meta_va, float(t))
    if ev["called_acc"] is None or ev["called_n"] < 8:
        continue
    if ev["called_acc"] > (best_ev["called_acc"] or 0):
        best_t, best_ev = float(t), ev
    if ev["called_acc"] >= 0.75:
        qualifying.append((float(t), ev))

if qualifying:
    best_t, best_ev = qualifying[0]  # lowest threshold clearing 75% on val

print(f"\nThreshold (val): {best_t:.2f} -> called "
      f"{best_ev['called_frac']*100:.0f}% @ {100*(best_ev['called_acc'] or 0):.1f}% "
      f"(n={best_ev['called_n']})")

ho_all = evaluate(X_ho_f, X_ho_r, meta_ho, 0.5)
ho = evaluate(X_ho_f, X_ho_r, meta_ho, best_t)

print("\n========= ECOMMERCE HOLDOUT (deployable protocol, untouched) =========")
print(f"All pairs:            {ho_all['overall_acc']*100:.1f}%  (n={ho_all['n']})")
print(f"Same-brand pairs:     {100*(ho_all['same_brand_acc'] or 0):.1f}%  (n={ho_all['same_brand_n']})")
print(f"Decisive pairs:       {100*(ho_all['decisive_acc'] or 0):.1f}%")
for label in ["<5pp", "5-10pp", "10-20pp", "20-30pp", "30pp+"]:
    g = ho_all.get(f"gap_{label}")
    if g:
        print(f"  gap {label:>7}:      {g['acc']*100:.1f}%  (n={g['n']})")
print(f"\nConfidence-gated @{best_t:.2f}:")
print(f"  calls made:         {ho['called_frac']*100:.1f}% (n={ho['called_n']})")
print(f"  accuracy on called: {100*(ho['called_acc'] or 0):.1f}%")
print(f"  decisive+called:    {100*(ho['decisive_called_acc'] or 0):.1f}%  (n={ho['decisive_called_n']})")
print(f"  same-brand+called:  {100*(ho['same_brand_called_acc'] or 0):.1f}%  (n={ho['same_brand_called_n']})")
print("=========================================================================")

import os
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
joblib.dump({
    "model_type": best_name,
    "mode": "deployable_ecommerce",
    "scaler": scaler,
    "model": model,
    "iso": iso,
    "threshold": best_t,
    "mean_feat": mean_feat,
    "visual_mean": visual_mean,
    "pca_mean": pca.mean_.astype(np.float32),
    "pca_components": pca.components_.astype(np.float32),
    "feature_names": FEATURE_NAMES,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "dim": DIM,
    "trained_on": f"tiktok_creative_center_ecommerce_{len(pairs)}_pairs_2026-07-12",
}, MODEL_PATH)
print(f"\nSaved artifact -> {MODEL_PATH}")

with open(EVAL_PATH, "w") as f:
    json.dump({
        "mode": "deployable_ecommerce",
        "split_sizes": {k: len(v) for k, v in split_pairs.items()},
        "val_scores": val_scores,
        "model": best_name,
        "threshold": best_t,
        "val_at_threshold": best_ev,
        "holdout_all": ho_all,
        "holdout_gated": ho,
    }, f, indent=2)
print(f"Saved eval -> {EVAL_PATH}")
