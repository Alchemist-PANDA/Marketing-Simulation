"""
End-to-end backtest of the ecommerce-tuned model through the REAL ABTestRunner
app path (randomized A/B position, visual features wired in), on the
194-pair ecommerce-only holdout. This is what a customer's app session
actually does, not an offline shortcut.
"""
import csv
import sys
import shutil
import numpy as np

sys.path.insert(0, "/home/user/Marketing-Simulation")

MODEL_PATH = "/home/user/Marketing-Simulation/models/creative_ranker.joblib"
CANDIDATE = "/home/user/Marketing-Simulation/models/creative_ranker_ecom_tuned.joblib"
BACKUP = "/home/user/Marketing-Simulation/models/creative_ranker_pre_ecom_backup.joblib"

shutil.copy(MODEL_PATH, BACKUP)
shutil.copy(CANDIDATE, MODEL_PATH)
print(f"Swapped in ecommerce-tuned model for this test run (backup at {BACKUP})")

from src.simulation.ab_test_runner import ABTestRunner
from src.agents.agent_generator import generate_population_arrays
from src.ai.creative_ranker import VISUAL_KEYS

PAIRS_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_validation_pairs.csv"
VF_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_visual_features.csv"

with open(PAIRS_PATH, encoding="utf-8") as f:
    pairs = [p for p in csv.DictReader(f) if p["split"] == "holdout"]

vf = {}
with open(VF_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vf[r["id"]] = {k: float(r[k]) for k in VISUAL_KEYS}

print(f"Ecommerce holdout pairs: {len(pairs)} (visual features for {len(vf)} ads)")

pop = generate_population_arrays(600, seed=42)
runner = ABTestRunner(master_population=pop, seed=42)

stats = {
    "total": 0, "called": 0, "called_correct": 0,
    "decisive_called": 0, "decisive_called_correct": 0,
    "same_brand_called": 0, "same_brand_called_correct": 0,
    "abstained": 0, "ranker_missing": 0,
}

rng = np.random.RandomState(7)
for i, p in enumerate(pairs):
    flip = rng.rand() < 0.5
    t1, t2 = (p["ad_b_text"], p["ad_a_text"]) if flip else (p["ad_a_text"], p["ad_b_text"])
    id1, id2 = (p["ad_b_id"], p["ad_a_id"]) if flip else (p["ad_a_id"], p["ad_b_id"])
    true_winner = "B" if flip else "A"

    vq = {}
    if id1 in vf:
        vq["A"] = vf[id1]
    if id2 in vf:
        vq["B"] = vf[id2]
    res = runner.run_test(t1, t2, objective="conversions",
                          visual_quality=vq or None)
    rk = res.get("ranker") or {}
    stats["total"] += 1
    if not rk.get("available"):
        stats["ranker_missing"] += 1
        continue
    if res["winner_source"] == "validated_model":
        stats["called"] += 1
        correct = res["winner"] == true_winner
        stats["called_correct"] += int(correct)
        if p["is_decisive"] == "True":
            stats["decisive_called"] += 1
            stats["decisive_called_correct"] += int(correct)
        if p["pair_type"] == "same_brand":
            stats["same_brand_called"] += 1
            stats["same_brand_called_correct"] += int(correct)
    else:
        stats["abstained"] += 1

print("\n========== ECOMMERCE END-TO-END (through real ABTestRunner) ==========")
print(f"Pairs tested:              {stats['total']}")
print(f"Confident calls:           {stats['called']} "
      f"({stats['called']/max(1,stats['total'])*100:.1f}%)")
print(f"Accuracy on called:        "
      f"{stats['called_correct']/max(1,stats['called'])*100:.1f}%  "
      f"({stats['called_correct']}/{stats['called']})")
print(f"Decisive+called:           {stats['decisive_called']}")
print(f"Accuracy decisive+called:  "
      f"{stats['decisive_called_correct']/max(1,stats['decisive_called'])*100:.1f}%")
print(f"Same-brand+called:         {stats['same_brand_called']}")
if stats["same_brand_called"]:
    print(f"Accuracy same-brand+called: "
          f"{stats['same_brand_called_correct']/stats['same_brand_called']*100:.1f}%")
else:
    print("Accuracy same-brand+called: n/a (0 called)")
print(f"Abstained (too close):     {stats['abstained']}")
print("=========================================================================")

from math import sqrt
def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0, center - half), min(1, center + half))

lo, hi = wilson_ci(stats["called_correct"], stats["called"])
print(f"\n95% Wilson CI on called accuracy: {lo*100:.1f}%-{hi*100:.1f}%")

shutil.copy(BACKUP, MODEL_PATH)
print(f"\nRestored original model to {MODEL_PATH} (this was a test run only)")
