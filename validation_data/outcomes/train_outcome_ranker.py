"""
Train a pairwise text ranker on REAL creative-dependent A/B outcomes
(within-test pairs, label = which creative actually got the higher rate).

This is the Option-A proof: unlike TikTok CTR tiers (targeting-driven,
~55% ceiling), within-test A/B pairs isolate the creative, so if the copy
carries signal the model should beat chance meaningfully. Reports the honest
ungated accuracy and the confidence/call-rate tradeoff on a test-id-split
holdout (no arm leakage).

Usage: python3 train_outcome_ranker.py <arms_csv> <pairs_csv> [out_model.joblib]
"""
import csv
import sys
from math import sqrt

import numpy as np

sys.path.insert(0, "/home/user/Marketing-Simulation")
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib

from src.ai.creative_ranker import engineered_features, FEATURE_NAMES, ProbaEnsemble

csv.field_size_limit(10_000_000)
ARMS = sys.argv[1] if len(sys.argv) > 1 else "/home/user/Marketing-Simulation/validation_data/outcomes/upworthy_arms.csv"
PAIRS = sys.argv[2] if len(sys.argv) > 2 else "/home/user/Marketing-Simulation/validation_data/outcomes/upworthy_pairs.csv"
OUT = sys.argv[3] if len(sys.argv) > 3 else "/home/user/Marketing-Simulation/models/creative_ranker_outcome_candidate.joblib"
N_PCA = 64

arms = {}
with open(ARMS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        arms[r["creative_id"]] = r
with open(PAIRS, encoding="utf-8") as f:
    pairs = list(csv.DictReader(f))
print(f"Arms: {len(arms)}, pairs: {len(pairs)}")

from sentence_transformers import SentenceTransformer
st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
ids = list(arms.keys())
texts = [arms[i]["creative_text"] for i in ids]
raw = st.encode(texts, batch_size=256, show_progress_bar=False, normalize_embeddings=True)

# PCA fit on TRAIN arms only
train_ids = {p["ad_a_id"] for p in pairs if p["split"] == "train"} | \
            {p["ad_b_id"] for p in pairs if p["split"] == "train"}
mask = np.array([i in train_ids for i in ids])
pca = PCA(n_components=N_PCA, random_state=42).fit(raw[mask])
emb = pca.transform(raw).astype(np.float32)
print(f"PCA-{N_PCA} explains {pca.explained_variance_ratio_.sum()*100:.1f}%")

feat = {}
for k, i in enumerate(ids):
    feat[i] = np.concatenate([emb[k], engineered_features(arms[i]["creative_text"])]).astype(np.float32)
DIM = len(next(iter(feat.values())))


def px(fa, fb):
    d = fa - fb
    return np.concatenate([d, np.abs(d)])


def mats(split):
    Xf, Xr, meta = [], [], []
    for p in pairs:
        if p["split"] != split:
            continue
        if p["ad_a_id"] not in feat or p["ad_b_id"] not in feat:
            continue
        fa, fb = feat[p["ad_a_id"]], feat[p["ad_b_id"]]
        Xf.append(px(fa, fb)); Xr.append(px(fb, fa)); meta.append(p)
    return np.array(Xf, dtype=np.float32), np.array(Xr, dtype=np.float32), meta


Xtr_f, Xtr_r, _ = mats("train")
Xva_f, Xva_r, meta_va = mats("val")
Xho_f, Xho_r, meta_ho = mats("holdout")
Xtr = np.concatenate([Xtr_f, Xtr_r]); ytr = np.concatenate([np.ones(len(Xtr_f)), np.zeros(len(Xtr_r))])
print(f"train pairs {len(Xtr_f)}, val {len(Xva_f)}, holdout {len(Xho_f)}")

scaler = StandardScaler().fit(Xtr)
Xtr_s = scaler.transform(Xtr)
cands = {
    "logreg_C0.1": LogisticRegression(C=0.1, max_iter=3000),
    "logreg_C1": LogisticRegression(C=1.0, max_iter=3000),
    "hgb": HistGradientBoostingClassifier(max_iter=600, learning_rate=0.05,
        max_leaf_nodes=31, l2_regularization=1.0, random_state=42),
}
for m in cands.values():
    m.fit(Xtr_s, ytr)
ens = ProbaEnsemble(list(cands.values()))


def avg_prob(m, Xf, Xr):
    pf = m.predict_proba(scaler.transform(Xf))[:, 1]
    pr = m.predict_proba(scaler.transform(Xr))[:, 1]
    return (pf + (1 - pr)) / 2.0


val_scores = {}
for name, m in list(cands.items()) + [("ensemble", ens)]:
    p = avg_prob(m, Xva_f, Xva_r)
    val_scores[name] = float((p >= 0.5).mean())
    print(f"val {name}: {val_scores[name]*100:.1f}%")
best = max(val_scores, key=val_scores.get)
model = ens if best == "ensemble" else cands[best]
print(f"Selected: {best}")


def wil(k, n, z=1.96):
    if n == 0: return (0, 0)
    ph = k / n; d = 1 + z*z/n; c = (ph + z*z/(2*n))/d
    h = z*sqrt(ph*(1-ph)/n + z*z/(4*n*n))/d
    return (max(0, c-h), min(1, c+h))


ph = avg_prob(model, Xho_f, Xho_r)
pred = (ph >= 0.5).astype(int); y = np.ones(len(ph), int)
conf = np.maximum(ph, 1-ph)
acc = (pred == y).mean()
lo, hi = wil(int((pred == y).sum()), len(y))
print(f"\n===== OUTCOME HOLDOUT (test-id split, no leakage) =====")
print(f"Ungated: {acc*100:.1f}%  (n={len(y)}, 95% CI {lo*100:.1f}-{hi*100:.1f})")
print(f"{'thresh':>7}{'call%':>7}{'n':>6}{'acc':>7}{'   95% CI':>14}")
best_t = 0.5
for t in [0.50, 0.55, 0.58, 0.60, 0.62, 0.65, 0.68, 0.70, 0.75]:
    m = conf >= t; n = int(m.sum())
    if n == 0: continue
    k = int((pred[m] == y[m]).sum()); a = k/n
    clo, chi = wil(k, n)
    print(f"{t:>7.2f}{100*m.mean():>7.1f}{n:>6}{100*a:>6.1f}%{100*clo:>7.1f}-{100*chi:<6.1f}")

# pick threshold on VAL for honesty
pv = avg_prob(model, Xva_f, Xva_r); cv = np.maximum(pv, 1-pv); predv = (pv >= 0.5).astype(int); yv = np.ones(len(pv), int)
sel_t, sel = 0.5, None
for t in np.arange(0.52, 0.80, 0.01):
    mm = cv >= t; nn = int(mm.sum())
    if nn < 40: continue
    a = (predv[mm] == yv[mm]).mean()
    if a >= 0.70:
        sel_t = float(t); break
print(f"\nVal-selected threshold (>=70% on val, n>=40): {sel_t:.2f}")

joblib.dump({
    "model_type": best, "mode": "outcome_ab", "scaler": scaler, "model": model,
    "iso": None, "threshold": sel_t,
    "pca_mean": pca.mean_.astype(np.float32),
    "pca_components": pca.components_.astype(np.float32),
    "feature_names": FEATURE_NAMES,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "visual_mean": None, "dim": DIM,
    "trained_on": f"ab_outcomes_{len(pairs)}_pairs",
}, OUT)
print(f"Saved -> {OUT}")
