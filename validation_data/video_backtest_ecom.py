"""
HEAVY VIDEO TEST: does the simulation pick the higher-CTR *video* creative?

For ecommerce holdout pairs where both ads have a live video URL, download
both real TikTok videos, run them through the exact app path
(video_features -> ABTestRunner.run_test with visual_quality), and measure
whether the confident calls match the real CTR-tier ground truth.

This is the video analogue of e2e_backtest_ecom.py. Bandwidth-bounded:
stops after MAX_PAIRS successfully-downloaded pairs. Expired CDN URLs
(older waves) are skipped, not counted.

Usage: python3 video_backtest_ecom.py [max_pairs]
"""
import csv
import os
import ssl
import sys
import urllib.request
from math import sqrt

import numpy as np

sys.path.insert(0, "/home/user/Marketing-Simulation")

MAX_PAIRS = int(sys.argv[1]) if len(sys.argv) > 1 else 50

ADS_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_ads_clean.csv"
PAIRS_PATH = "/home/user/Marketing-Simulation/validation_data/ecommerce_validation_pairs.csv"

ctx = ssl.create_default_context()
ca = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(ca):
    ctx.load_verify_locations(ca)

with open(ADS_PATH, encoding="utf-8") as f:
    ads = {r["id"]: r for r in csv.DictReader(f)}
with open(PAIRS_PATH, encoding="utf-8") as f:
    pairs = [p for p in csv.DictReader(f) if p["split"] == "holdout"]

# only pairs where BOTH ads have a video URL
vid_pairs = [p for p in pairs
             if ads.get(p["ad_a_id"], {}).get("video_url_720p", "").startswith("http")
             and ads.get(p["ad_b_id"], {}).get("video_url_720p", "").startswith("http")]
print(f"Ecommerce holdout pairs with both video URLs: {len(vid_pairs)}/{len(pairs)}")

from src.simulation.ab_test_runner import ABTestRunner
from src.agents.agent_generator import generate_population_arrays
from src.ai.visual_features import video_features

_vid_cache = {}


def get_video_features(ad_id):
    if ad_id in _vid_cache:
        return _vid_cache[ad_id]
    url = ads[ad_id]["video_url_720p"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            data = r.read()
        rep = video_features(data)
        rep = rep if rep.get("available") else None
    except Exception:
        rep = None
    _vid_cache[ad_id] = rep
    return rep


pop = generate_population_arrays(600, seed=42)
runner = ABTestRunner(master_population=pop, seed=42)

stats = {"tested": 0, "called": 0, "called_correct": 0,
         "decisive_called": 0, "decisive_called_correct": 0,
         "abstained": 0, "skipped_dl": 0, "keyframe_ok": 0}

rng = np.random.RandomState(7)
for p in vid_pairs:
    if stats["tested"] >= MAX_PAIRS:
        break
    fa = get_video_features(p["ad_a_id"])
    fb = get_video_features(p["ad_b_id"])
    if fa is None or fb is None:
        stats["skipped_dl"] += 1
        continue
    if fa.get("keyframe_features"):
        stats["keyframe_ok"] += 1
    if fb.get("keyframe_features"):
        stats["keyframe_ok"] += 1

    flip = rng.rand() < 0.5
    t1, t2 = (p["ad_b_text"], p["ad_a_text"]) if flip else (p["ad_a_text"], p["ad_b_text"])
    v1, v2 = (fb, fa) if flip else (fa, fb)
    true_winner = "B" if flip else "A"

    res = runner.run_test(t1, t2, objective="conversions",
                          visual_quality={"A": v1, "B": v2})
    rk = res.get("ranker") or {}
    stats["tested"] += 1
    if not rk.get("available"):
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
    if stats["tested"] % 10 == 0:
        ca_ = stats["called_correct"] / max(1, stats["called"]) * 100
        print(f"  tested={stats['tested']} called={stats['called']} "
              f"acc={ca_:.1f}% (dl_skipped={stats['skipped_dl']})", flush=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


print("\n========== VIDEO END-TO-END (real TikTok videos, app path) ==========")
print(f"Pairs tested (both videos downloaded): {stats['tested']}")
print(f"Videos with keyframe features extracted: {stats['keyframe_ok']}")
print(f"Confident calls:        {stats['called']} "
      f"({stats['called']/max(1,stats['tested'])*100:.1f}%)")
print(f"Accuracy on called:     {stats['called_correct']/max(1,stats['called'])*100:.1f}% "
      f"({stats['called_correct']}/{stats['called']})")
lo, hi = wilson(stats["called_correct"], stats["called"])
if lo is not None:
    print(f"  95% CI:               {lo*100:.1f}%-{hi*100:.1f}%")
print(f"Decisive+called acc:    "
      f"{stats['decisive_called_correct']/max(1,stats['decisive_called'])*100:.1f}% "
      f"(n={stats['decisive_called']})")
print(f"Abstained:              {stats['abstained']}")
print(f"Pairs skipped (expired/failed download): {stats['skipped_dl']}")
print("=====================================================================")
