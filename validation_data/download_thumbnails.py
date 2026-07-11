"""
Download TikTok ad cover thumbnails for visual-feature training.
Bandwidth only — no API cost. Failures are skipped; features default later.
Saves per-ad visual features to visual_features.csv.
"""

import csv
import io
import os
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/user/Marketing-Simulation")
from src.ai.visual_features import image_features

ADS_PATH = "/home/user/Marketing-Simulation/validation_data/tiktok_ads_clean.csv"
OUT_PATH = "/home/user/Marketing-Simulation/validation_data/visual_features.csv"

ctx = ssl.create_default_context()
ca = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(ca):
    ctx.load_verify_locations(ca)

with open(ADS_PATH, encoding="utf-8") as f:
    ads = list(csv.DictReader(f))

targets = [(a["id"], a["video_cover"]) for a in ads if a.get("video_cover")]
print(f"Ads with cover URL: {len(targets)}/{len(ads)}")


def fetch(item):
    ad_id, url = item
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = r.read()
        rep = image_features(data)
        if rep.get("available"):
            return ad_id, rep
    except Exception:
        pass
    return ad_id, None


rows = []
ok = 0
with ThreadPoolExecutor(max_workers=24) as ex:
    futures = [ex.submit(fetch, t) for t in targets]
    for i, fut in enumerate(as_completed(futures)):
        ad_id, rep = fut.result()
        if rep:
            ok += 1
            rows.append({
                "id": ad_id,
                "vf_brightness": rep["brightness"],
                "vf_contrast": rep["contrast"],
                "vf_colorfulness": rep["colorfulness"],
                "vf_edge_density": rep["edge_density"],
                "vf_aspect": rep["aspect_ratio"],
                "vf_quality": rep["visual_quality"],
            })
        if (i + 1) % 400 == 0:
            print(f"  {i+1}/{len(targets)} done ({ok} ok)")

print(f"Downloaded + featurized {ok}/{len(targets)} thumbnails")
with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "vf_brightness", "vf_contrast",
                                      "vf_colorfulness", "vf_edge_density",
                                      "vf_aspect", "vf_quality"])
    w.writeheader()
    w.writerows(rows)
print(f"Saved -> {OUT_PATH}")
