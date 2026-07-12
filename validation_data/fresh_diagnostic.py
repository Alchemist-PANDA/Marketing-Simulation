"""Diagnostic: what does the model predict on fresh pairs REGARDLESS of the
confidence gate, so we can see if there's real (if under-confident) signal
or if it's actually noise on this fresh distribution."""
import csv
import sys
import numpy as np

sys.path.insert(0, "/home/user/Marketing-Simulation")
from src.ai.creative_ranker import compare, VISUAL_KEYS

PAIRS_PATH = "/home/user/Marketing-Simulation/validation_data/fresh_validation_pairs.csv"
VF_PATH = "/home/user/Marketing-Simulation/validation_data/fresh_visual_features.csv"

with open(PAIRS_PATH, encoding="utf-8") as f:
    pairs = list(csv.DictReader(f))
vf = {}
with open(VF_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vf[r["id"]] = {k: float(r[k]) for k in VISUAL_KEYS}

rng = np.random.RandomState(11)
correct_ungated = 0
confs = []
n = 0
for p in pairs:
    flip = rng.rand() < 0.5
    t1, t2 = (p["ad_b_text"], p["ad_a_text"]) if flip else (p["ad_a_text"], p["ad_b_text"])
    id1, id2 = (p["ad_b_id"], p["ad_a_id"]) if flip else (p["ad_a_id"], p["ad_b_id"])
    true_winner = "B" if flip else "A"
    vq1 = vf.get(id1)
    vq2 = vf.get(id2)
    res = compare(t1, t2, visual_a=vq1, visual_b=vq2)
    if not res.get("available"):
        continue
    n += 1
    pred_winner = res["winner"]
    confs.append(res["confidence"])
    correct_ungated += int(pred_winner == true_winner)

print(f"n={n}")
print(f"Ungated (always-call) accuracy: {correct_ungated/n*100:.1f}%")
confs = np.array(confs)
print(f"Confidence distribution: min={confs.min():.3f} p25={np.percentile(confs,25):.3f} "
      f"median={np.median(confs):.3f} p75={np.percentile(confs,75):.3f} max={confs.max():.3f}")
print(f"Fraction >= 0.72 threshold: {(confs>=0.72).mean()*100:.1f}%")
print(f"Fraction >= 0.60: {(confs>=0.60).mean()*100:.1f}%")
print(f"Fraction >= 0.55: {(confs>=0.55).mean()*100:.1f}%")
