"""
Build validation dataset (v2) from all Apify TikTok Creative Center scrapes.

Reads every persisted tool-result JSON file, deduplicates by ad ID, creates
ad pairs (same-brand and same-industry), and writes CSVs for training and
backtesting. v2 changes: merges the new ~2k-ad scrape wave, keeps
video_cover/video_url_720p for future visual training, and pairs far more
aggressively (the v1 5-pairs-per-industry cap threw away most of the signal).

CTR ground truth: TikTok CTR percentile tier (0.01 = Top 1% = best).
"""

import json
import csv
import os
import glob
import random
from collections import Counter

RESULTS_DIR = (
    "/root/.claude/projects/-home-user-Marketing-Simulation/"
    "a6a16d5d-152a-5a09-8ed4-0ec5de802d49/tool-results"
)
OUT_DIR = "/home/user/Marketing-Simulation/validation_data"

random.seed(42)

all_ads = {}
for fpath in sorted(glob.glob(os.path.join(RESULTS_DIR, "*.txt"))):
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        continue
    for item in data.get("items", []):
        ad_id = item.get("id", "")
        ad_title = (item.get("ad_title") or "").strip()
        if not ad_id or not ad_title or len(ad_title) < 10:
            continue
        if ad_id not in all_ads:
            all_ads[ad_id] = item

print(f"Total unique ads with text >= 10 chars: {len(all_ads)}")


def is_english_text(text):
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / max(1, len(text)) > 0.7


ads = []
for ad_id, item in all_ads.items():
    title = item.get("ad_title", "")
    if not is_english_text(title):
        continue
    ctr = item.get("ctr", 0)
    if not ctr or ctr <= 0:
        continue
    ads.append({
        "id": ad_id,
        "ad_title": title,
        "brand_name": (item.get("brand_name") or "").strip(),
        "likes": item.get("like", 0),
        "ctr_percentile": ctr,
        "ctr_readable": item.get("ctr_readable", ""),
        "industry": item.get("industry", ""),
        "objective": item.get("objective", ""),
        "video_duration": item.get("video_duration", 0),
        "video_cover": item.get("video_cover", ""),
        "video_url_720p": item.get("video_url_720p", ""),
    })

print(f"After English + valid CTR filter: {len(ads)}")
industry_dist = Counter(a["industry"] for a in ads)
print(f"Industries covered: {len(industry_dist)}")

# ------------------------------------------------------------- splits
# Assign each ad to a split FIRST (by brand-group hash), then pair only
# within splits. v2 fix: pairing before splitting wasted ~1,800 pairs.
import hashlib


def bucket_of_ad(ad):
    group = ad["brand_name"].strip().lower() or f"ad_{ad['id']}"
    h = int(hashlib.md5(group.encode()).hexdigest(), 16) % 100
    return "train" if h < 60 else ("val" if h < 80 else "holdout")


for ad in ads:
    ad["split"] = bucket_of_ad(ad)

from collections import Counter as _C
print(f"Ad splits: {_C(a['split'] for a in ads)}")


# ---------------------------------------------------------------- pairs
def make_pair(a, b, pair_type):
    """a must be the better ad (lower ctr percentile)."""
    return {
        "split": a["split"],
        "pair_type": pair_type,
        "brand": a["brand_name"] or a["industry"],
        "industry": a["industry"],
        "ad_a_id": a["id"], "ad_a_text": a["ad_title"],
        "ad_a_ctr_pct": a["ctr_percentile"], "ad_a_ctr_label": a["ctr_readable"],
        "ad_a_likes": a["likes"],
        "ad_b_id": b["id"], "ad_b_text": b["ad_title"],
        "ad_b_ctr_pct": b["ctr_percentile"], "ad_b_ctr_label": b["ctr_readable"],
        "ad_b_likes": b["likes"],
        "winner_ground_truth": "A",
        "ctr_gap": round(abs(b["ctr_percentile"] - a["ctr_percentile"]), 4),
    }


# Same-brand pairs: every combination with a CTR-tier difference
brand_groups = {}
for ad in ads:
    if ad["brand_name"]:
        brand_groups.setdefault(ad["brand_name"], []).append(ad)

brand_pairs = []
for brand, group in brand_groups.items():
    group.sort(key=lambda x: x["ctr_percentile"])
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            a, b = group[i], group[j]
            if a["ctr_percentile"] != b["ctr_percentile"] \
                    and a["ad_title"].strip() != b["ad_title"].strip() \
                    and a["split"] == b["split"]:
                brand_pairs.append(make_pair(a, b, "same_brand"))

print(f"Same-brand pairs: {len(brand_pairs)}")

# Same-industry pairs: aggressive sampling, up to 60 per industry,
# preferring larger gaps but including close races too.
industry_groups = {}
for ad in ads:
    if ad["industry"]:
        industry_groups.setdefault(ad["industry"], []).append(ad)

industry_pairs = []
for ind, group in industry_groups.items():
    if len(group) < 2:
        continue
    group = sorted(group, key=lambda x: x["ctr_percentile"])
    candidates = []
    n = len(group)
    for _ in range(min(400, n * 4)):
        a = random.choice(group)
        b = random.choice(group)
        if a["id"] == b["id"] or a["ctr_percentile"] == b["ctr_percentile"]:
            continue
        if a["ad_title"].strip() == b["ad_title"].strip():
            continue
        if a["split"] != b["split"]:
            continue
        if a["ctr_percentile"] > b["ctr_percentile"]:
            a, b = b, a
        candidates.append(make_pair(a, b, "same_industry"))
    # dedupe within industry, keep up to 60 preferring big gaps
    seen = set()
    uniq = []
    for p in sorted(candidates, key=lambda x: -x["ctr_gap"]):
        key = tuple(sorted([p["ad_a_id"], p["ad_b_id"]]))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    # 70% big-gap, 30% random of remainder for diversity
    keep = uniq[:42]
    rest = uniq[42:]
    random.shuffle(rest)
    keep += rest[:18]
    industry_pairs.extend(keep)

print(f"Same-industry pairs: {len(industry_pairs)}")

# merge + dedupe
seen = set()
unique_pairs = []
for p in brand_pairs + industry_pairs:
    key = tuple(sorted([p["ad_a_id"], p["ad_b_id"]]))
    if key not in seen:
        seen.add(key)
        unique_pairs.append(p)

for p in unique_pairs:
    p["is_decisive"] = p["ctr_gap"] >= 0.10

decisive = sum(1 for p in unique_pairs if p["is_decisive"])
print(f"\nTotal unique pairs: {len(unique_pairs)}")
print(f"  Decisive (gap >= 10pp): {decisive}")
print(f"  Close (gap < 10pp):     {len(unique_pairs) - decisive}")

# ------------------------------------------------------------------ write
ads_path = os.path.join(OUT_DIR, "tiktok_ads_clean.csv")
with open(ads_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "ad_title", "brand_name", "likes", "ctr_percentile",
        "ctr_readable", "industry", "objective", "video_duration",
        "video_cover", "video_url_720p", "split",
    ])
    writer.writeheader()
    writer.writerows(ads)
print(f"\nSaved {len(ads)} ads -> {ads_path}")

pairs_path = os.path.join(OUT_DIR, "validation_pairs.csv")
with open(pairs_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(unique_pairs[0].keys()))
    writer.writeheader()
    writer.writerows(unique_pairs)
print(f"Saved {len(unique_pairs)} pairs -> {pairs_path}")
