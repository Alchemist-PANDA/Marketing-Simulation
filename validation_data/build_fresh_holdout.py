"""
Build a FRESH holdout set from ads that never appeared in the original
2,489-ad training corpus. This is a pure generalization test: no retraining,
no leakage, brand-new advertisers/campaigns scraped from Creative Center
(30-day CTR-ordered and 180-day like-ordered top-ads leaderboards).

Pairing follows the same protocol as build_validation_dataset.py (same-brand
+ same-industry, CTR-tier ground truth) but everything lands in a single
"fresh_holdout" split since none of it is used for training.
"""

import json
import csv
import os
import random
from collections import Counter

OUT_DIR = "/home/user/Marketing-Simulation/validation_data"
random.seed(7)

with open(os.path.join(OUT_DIR, "fresh_ads_raw.json"), encoding="utf-8") as f:
    raw = json.load(f)

print(f"Raw fresh items: {len(raw)}")


def is_english_text(text):
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / max(1, len(text)) > 0.7


ads = []
seen_ids = set()
for item in raw:
    ad_id = item.get("id", "")
    title = (item.get("ad_title") or "").strip()
    if not ad_id or not title or len(title) < 10 or ad_id in seen_ids:
        continue
    if not is_english_text(title):
        continue
    ctr = item.get("ctr", 0)
    if not ctr or ctr <= 0:
        continue
    seen_ids.add(ad_id)
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
        "split": "fresh_holdout",
    })

print(f"After English + valid CTR filter: {len(ads)}")
industry_dist = Counter(a["industry"] for a in ads)
print(f"Industries covered: {len(industry_dist)}")


def make_pair(a, b, pair_type):
    return {
        "split": "fresh_holdout",
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
                    and a["ad_title"].strip() != b["ad_title"].strip():
                brand_pairs.append(make_pair(a, b, "same_brand"))

print(f"Same-brand pairs: {len(brand_pairs)}")

industry_groups = {}
for ad in ads:
    if ad["industry"]:
        industry_groups.setdefault(ad["industry"], []).append(ad)

industry_pairs = []
for ind, group in industry_groups.items():
    if len(group) < 2:
        continue
    n = len(group)
    candidates = []
    for _ in range(min(400, n * 6)):
        a = random.choice(group)
        b = random.choice(group)
        if a["id"] == b["id"] or a["ctr_percentile"] == b["ctr_percentile"]:
            continue
        if a["ad_title"].strip() == b["ad_title"].strip():
            continue
        if a["ctr_percentile"] > b["ctr_percentile"]:
            a, b = b, a
        candidates.append(make_pair(a, b, "same_industry"))
    seen = set()
    uniq = []
    for p in sorted(candidates, key=lambda x: -x["ctr_gap"]):
        key = tuple(sorted([p["ad_a_id"], p["ad_b_id"]]))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    keep = uniq[:42]
    rest = uniq[42:]
    random.shuffle(rest)
    keep += rest[:18]
    industry_pairs.extend(keep)

print(f"Same-industry pairs: {len(industry_pairs)}")

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
print(f"\nTotal unique fresh pairs: {len(unique_pairs)}")
print(f"  Decisive (gap >= 10pp): {decisive}")
print(f"  Close (gap < 10pp):     {len(unique_pairs) - decisive}")

ads_path = os.path.join(OUT_DIR, "fresh_ads_clean.csv")
with open(ads_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "ad_title", "brand_name", "likes", "ctr_percentile",
        "ctr_readable", "industry", "objective", "video_duration",
        "video_cover", "video_url_720p", "split",
    ])
    writer.writeheader()
    writer.writerows(ads)
print(f"\nSaved {len(ads)} ads -> {ads_path}")

pairs_path = os.path.join(OUT_DIR, "fresh_validation_pairs.csv")
if unique_pairs:
    with open(pairs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(unique_pairs[0].keys()))
        writer.writeheader()
        writer.writerows(unique_pairs)
    print(f"Saved {len(unique_pairs)} pairs -> {pairs_path}")
else:
    print("WARNING: no pairs generated")
