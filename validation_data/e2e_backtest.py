"""
End-to-end backtest: run HOLDOUT pairs through the actual ABTestRunner
(the exact code path the app uses), and measure:
- winner accuracy on called pairs (the product's confident verdicts)
- abstention rate
- image feature pipeline smoke test

This is the final Phase 5 gate. Ground truth: ad_a is the better ad.
"""

import csv
import sys
import numpy as np

sys.path.insert(0, "/home/user/Marketing-Simulation")

from src.simulation.ab_test_runner import ABTestRunner
from src.agents.agent_generator import generate_population_arrays
from src.ai.creative_ranker import VISUAL_KEYS

PAIRS_PATH = "/home/user/Marketing-Simulation/validation_data/validation_pairs.csv"
VF_PATH = "/home/user/Marketing-Simulation/validation_data/visual_features.csv"

with open(PAIRS_PATH, encoding="utf-8") as f:
    pairs = [p for p in csv.DictReader(f) if p["split"] == "holdout"]

vf = {}
with open(VF_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vf[r["id"]] = {k: float(r[k]) for k in VISUAL_KEYS}

print(f"Holdout pairs: {len(pairs)} (visual features for {len(vf)} ads)")

pop = generate_population_arrays(600, seed=42)
runner = ABTestRunner(master_population=pop, seed=42)

stats = {
    "total": 0, "called": 0, "called_correct": 0,
    "decisive_called": 0, "decisive_called_correct": 0,
    "abstained": 0, "ranker_missing": 0,
}

rng = np.random.RandomState(7)
for i, p in enumerate(pairs):
    # randomize which side is "A" so positional bias can't help
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
    else:
        stats["abstained"] += 1

    if (i + 1) % 50 == 0:
        ca = stats["called_correct"] / max(1, stats["called"]) * 100
        print(f"  {i+1}/{len(pairs)} | called acc so far: {ca:.1f}% "
              f"({stats['called']} called, {stats['abstained']} abstained)")

print("\n========== END-TO-END (through ABTestRunner) ==========")
print(f"Pairs tested:            {stats['total']}")
print(f"Ranker available:        {stats['total'] - stats['ranker_missing']}")
print(f"Confident calls:         {stats['called']} "
      f"({stats['called']/max(1,stats['total'])*100:.1f}%)")
print(f"Accuracy on called:      "
      f"{stats['called_correct']/max(1,stats['called'])*100:.1f}%")
print(f"Decisive called:         {stats['decisive_called']}")
print(f"Accuracy decisive+called: "
      f"{stats['decisive_called_correct']/max(1,stats['decisive_called'])*100:.1f}%")
print(f"Abstained (too close):   {stats['abstained']}")
print("========================================================")

# --- image pipeline smoke test ---
from PIL import Image
import io
from src.ai.visual_features import image_features
buf = io.BytesIO()
Image.new("RGB", (540, 960), (200, 60, 90)).save(buf, format="PNG")
rep = image_features(buf.getvalue())
print(f"\nImage pipeline smoke test: available={rep['available']}, "
      f"visual_quality={rep['visual_quality']}, vertical={rep['is_vertical']}")

from src.ai.visual_features import video_features
vrep = video_features(b"not-a-real-video")
print(f"Video pipeline graceful fallback: available={vrep['available']} (expected False here; True on Streamlit Cloud with opencv)")
