"""
Keep the v5 model (trained on the full 2,887-pair mixed corpus — more data,
better-generalizing embeddings/weights) but re-tune ONLY the confidence
threshold using ecommerce-specific validation pairs, so the abstention cutoff
is calibrated for ecommerce ad copy specifically instead of borrowed from the
mixed-industry val set. This isolates "does the model need retraining" (no,
per compare_v5_on_ecom.py) from "does the threshold need retuning for this
vertical" (this script answers that).
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
OUT_MODEL = "/home/user/Marketing-Simulation/models/creative_ranker_ecom_tuned.joblib"

with open(ADS_PATH, encoding="utf-8") as f:
    ads = {r["id"]: r for r in csv.DictReader(f)}
with open(PAIRS_PATH, encoding="utf-8") as f:
    all_pairs = list(csv.DictReader(f))
vf = {}
with open(VF_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vf[r["id"]] = {k: float(r[k]) for k in VISUAL_KEYS}

art = joblib.load(V5_MODEL)
scaler, model, iso = art["scaler"], art["model"], art["iso"]

from sentence_transformers import SentenceTransformer
st_model = SentenceTransformer(art["embedding_model"])
ad_ids = list(ads.keys())
texts = [ads[i]["ad_title"] for i in ad_ids]
raw_emb = st_model.encode(texts, batch_size=128, show_progress_bar=False,
                          normalize_embeddings=True)
emb = (raw_emb - art["pca_mean"]) @ art["pca_components"].T
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


def make_matrices(plist):
    Xf, Xr, meta = [], [], []
    for p in plist:
        fa, fb = feat[p["ad_a_id"]], feat[p["ad_b_id"]]
        Xf.append(pair_x(fa, fb))
        Xr.append(pair_x(fb, fa))
        meta.append(p)
    return np.array(Xf, dtype=np.float32), np.array(Xr, dtype=np.float32), meta


def avg_prob(Xf, Xr):
    pf = model.predict_proba(scaler.transform(Xf))[:, 1]
    pr = model.predict_proba(scaler.transform(Xr))[:, 1]
    return (pf + (1.0 - pr)) / 2.0


def evaluate(Xf, Xr, meta, threshold):
    p = iso.predict(avg_prob(Xf, Xr))
    conf = np.maximum(p, 1 - p)
    called = conf >= threshold
    pred = (p >= 0.5).astype(int)
    y = np.ones(len(p), dtype=int)
    dec = np.array([m["is_decisive"] == "True" for m in meta])
    sb = np.array([m["pair_type"] == "same_brand" for m in meta])

    def acc(mask):
        return float((pred[mask] == y[mask]).mean()) if mask.any() else None

    return {
        "called_frac": float(called.mean()), "called_n": int(called.sum()),
        "called_acc": acc(called),
        "decisive_called_acc": acc(dec & called), "decisive_called_n": int((dec & called).sum()),
        "same_brand_called_acc": acc(sb & called), "same_brand_called_n": int((sb & called).sum()),
    }


ecom_val = [p for p in all_pairs if p["split"] == "val"]
ecom_holdout = [p for p in all_pairs if p["split"] == "holdout"]
print(f"Ecommerce val pairs: {len(ecom_val)}, holdout pairs: {len(ecom_holdout)}")

Xv_f, Xv_r, meta_v = make_matrices(ecom_val)
Xh_f, Xh_r, meta_h = make_matrices(ecom_holdout)

print("\nThreshold sweep on ECOMMERCE VAL (choosing the highest-call-rate "
      "threshold that clears 75% val accuracy with n>=15 called):")
best_t, best_ev = None, None
for t in np.arange(0.50, 0.97, 0.01):
    ev = evaluate(Xv_f, Xv_r, meta_v, float(t))
    if ev["called_n"] < 15 or ev["called_acc"] is None:
        continue
    marker = ""
    if ev["called_acc"] >= 0.75 and best_t is None:
        best_t, best_ev = float(t), ev
        marker = "  <== selected"
    if t in (0.50, 0.60, 0.65, 0.70, 0.72, 0.75, 0.80, 0.85):
        print(f"  t={t:.2f}: call_rate={ev['called_frac']*100:5.1f}% "
              f"n={ev['called_n']:3d}  acc={100*(ev['called_acc'] or 0):5.1f}%{marker}")

if best_t is None:
    print("No threshold cleared 75% on ecommerce val with n>=15 -- falling back to v5's threshold")
    best_t = art["threshold"]

print(f"\nSelected ecommerce-tuned threshold: {best_t:.2f}")

ho_at_v5 = evaluate(Xh_f, Xh_r, meta_h, art["threshold"])
ho_at_new = evaluate(Xh_f, Xh_r, meta_h, best_t)

print(f"\n===== ECOMMERCE HOLDOUT ({len(ecom_holdout)} pairs) =====")
print(f"At v5's original threshold ({art['threshold']:.2f}):")
print(f"  call_rate={ho_at_v5['called_frac']*100:.1f}% n={ho_at_v5['called_n']} "
      f"acc={100*(ho_at_v5['called_acc'] or 0):.1f}%  "
      f"decisive+called={100*(ho_at_v5['decisive_called_acc'] or 0):.1f}% (n={ho_at_v5['decisive_called_n']})  "
      f"same-brand+called={100*(ho_at_v5['same_brand_called_acc'] or 0):.1f}% (n={ho_at_v5['same_brand_called_n']})")
print(f"At ecommerce-tuned threshold ({best_t:.2f}):")
print(f"  call_rate={ho_at_new['called_frac']*100:.1f}% n={ho_at_new['called_n']} "
      f"acc={100*(ho_at_new['called_acc'] or 0):.1f}%  "
      f"decisive+called={100*(ho_at_new['decisive_called_acc'] or 0):.1f}% (n={ho_at_new['decisive_called_n']})  "
      f"same-brand+called={100*(ho_at_new['same_brand_called_acc'] or 0):.1f}% (n={ho_at_new['same_brand_called_n']})")

# Wilson 95% CI for the winning config
from math import sqrt


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0, center - half), min(1, center + half))


chosen = ho_at_new if ho_at_new["called_n"] >= ho_at_v5["called_n"] else ho_at_v5
k = round((chosen["called_acc"] or 0) * chosen["called_n"])
lo, hi = wilson_ci(k, chosen["called_n"])
print(f"\n95% Wilson CI on called accuracy: {lo*100:.1f}%-{hi*100:.1f}% "
      f"({k}/{chosen['called_n']} correct)")

art_new = dict(art)
art_new["threshold"] = best_t
art_new["mode"] = "deployable_ecommerce_tuned"
art_new["trained_on"] = art["trained_on"] + "_threshold_tuned_on_ecommerce_val"
joblib.dump(art_new, OUT_MODEL)
print(f"\nSaved ecommerce-threshold-tuned artifact -> {OUT_MODEL}")
