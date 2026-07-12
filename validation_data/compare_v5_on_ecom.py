"""
Does the ecommerce-only retrain actually beat the shipped v5 model (trained on
the full mixed-industry corpus) when BOTH are scored on the exact same
194-pair ecommerce holdout? This is the real test of whether specializing
helped or hurt.
"""
import csv
import sys
import numpy as np
import joblib

sys.path.insert(0, "/home/user/Marketing-Simulation")
from src.ai.creative_ranker import engineered_features, visual_vector, VISUAL_KEYS

ADS_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_ads_clean.csv"
PAIRS_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_validation_pairs.csv"
VF_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_visual_features.csv"
V5_MODEL = "/home/user/Marketing-Simulation/models/creative_ranker.joblib"

with open(ADS_PATH, encoding="utf-8") as f:
    ads = {r["id"]: r for r in csv.DictReader(f)}
with open(PAIRS_PATH, encoding="utf-8") as f:
    pairs = [p for p in csv.DictReader(f) if p["split"] == "holdout"]
vf = {}
with open(VF_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vf[r["id"]] = {k: float(r[k]) for k in VISUAL_KEYS}

art = joblib.load(V5_MODEL)
print(f"Loaded v5 model: {art['model_type']}, threshold={art['threshold']}")

from sentence_transformers import SentenceTransformer
st_model = SentenceTransformer(art["embedding_model"])
ad_ids = list(ads.keys())
texts = [ads[i]["ad_title"] for i in ad_ids]
raw_emb = st_model.encode(texts, batch_size=128, show_progress_bar=False,
                          normalize_embeddings=True)
pca_mean, pca_comp = art["pca_mean"], art["pca_components"]
emb = (raw_emb - pca_mean) @ pca_comp.T

_art_visual = {"visual_mean": art["visual_mean"]}


def ad_visual(aid):
    return visual_vector(vf.get(aid), _art_visual)


feat = {}
for k, aid in enumerate(ad_ids):
    a = ads[aid]
    feat[aid] = np.concatenate([
        emb[k],
        engineered_features(a["ad_title"]),
        np.array([np.log1p(max(0.0, float(a["video_duration"] or 0)))], dtype=np.float32),
        ad_visual(aid),
    ]).astype(np.float32)


def pair_x(fa, fb):
    d = fa - fb
    return np.concatenate([d, np.abs(d)])


Xf, Xr, meta = [], [], []
for p in pairs:
    fa, fb = feat[p["ad_a_id"]], feat[p["ad_b_id"]]
    Xf.append(pair_x(fa, fb))
    Xr.append(pair_x(fb, fa))
    meta.append(p)
Xf, Xr = np.array(Xf, dtype=np.float32), np.array(Xr, dtype=np.float32)

scaler, model, iso, threshold = art["scaler"], art["model"], art["iso"], art["threshold"]
pf = model.predict_proba(scaler.transform(Xf))[:, 1]
pr = model.predict_proba(scaler.transform(Xr))[:, 1]
avg = (pf + (1.0 - pr)) / 2.0
p = iso.predict(avg)
conf = np.maximum(p, 1 - p)
called = conf >= threshold
pred = (p >= 0.5).astype(int)
y = np.ones(len(p), dtype=int)
dec = np.array([m["is_decisive"] == "True" for m in meta])
sb = np.array([m["pair_type"] == "same_brand" for m in meta])


def acc(mask):
    return float((pred[mask] == y[mask]).mean()) if mask.any() else None


print(f"\n===== v5 (mixed-industry model) scored on the {len(pairs)}-pair ECOMMERCE holdout =====")
print(f"All pairs (ungated):     {acc(np.ones(len(y),bool))*100:.1f}%  (n={len(y)})")
print(f"Same-brand (ungated):    {100*(acc(sb) or 0):.1f}%  (n={sb.sum()})")
print(f"Decisive (ungated):      {100*(acc(dec) or 0):.1f}%")
print(f"\nConfidence-gated @ v5's own threshold ({threshold:.2f}):")
print(f"  calls made:            {called.mean()*100:.1f}% (n={called.sum()})")
print(f"  accuracy on called:    {100*(acc(called) or 0):.1f}%")
dc = dec & called
print(f"  decisive+called:       {100*(acc(dc) or 0):.1f}%  (n={dc.sum()})")
sbc = sb & called
print(f"  same-brand+called:     {100*(acc(sbc) or 0):.1f}%  (n={sbc.sum()})")
