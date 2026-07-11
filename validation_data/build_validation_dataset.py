"""
Build validation dataset from Apify TikTok Creative Center scrapes.

Reads persisted tool-result JSON files, deduplicates by ad ID,
creates ad pairs (brand-based and industry-based), and writes
a CSV ready for the simulator backtest.

CTR field from TikTok Creative Center: 0.01 = "Top 1%" (best),
0.50 = "Top 50%" (median). LOWER = better performing ad.
"""

import json
import csv
import os
import glob

RESULTS_DIR = (
    "/root/.claude/projects/-home-user-Marketing-Simulation/"
    "a6a16d5d-152a-5a09-8ed4-0ec5de802d49/tool-results"
)
OUT_DIR = "/home/user/Marketing-Simulation/validation_data"

all_ads = {}

for fpath in sorted(glob.glob(os.path.join(RESULTS_DIR, "*.txt"))):
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        continue

    items = data.get("items", [])
    for item in items:
        ad_id = item.get("id", "")
        ad_title = (item.get("ad_title") or "").strip()
        if not ad_id or not ad_title or len(ad_title) < 10:
            continue
        if ad_id not in all_ads:
            all_ads[ad_id] = item

print(f"Total unique ads with text >= 10 chars: {len(all_ads)}")

# Filter to English-ish ads (basic heuristic: mostly ASCII)
def is_english_text(text):
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / max(1, len(text)) > 0.7

ads = []
for ad_id, item in all_ads.items():
    title = item.get("ad_title", "")
    if not is_english_text(title):
        continue
    ctr = item.get("ctr", 0)
    if ctr <= 0:
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
    })

print(f"After English + valid CTR filter: {len(ads)}")

# --- Stats ---
from collections import Counter
ctr_dist = Counter(a["ctr_readable"] for a in ads)
industry_dist = Counter(a["industry"] for a in ads)

print("\nCTR tier distribution:")
for tier, count in sorted(ctr_dist.items(), key=lambda x: float(x[0].replace("Top ", "").replace("%", "")) if x[0].startswith("Top") else 999):
    print(f"  {tier}: {count}")

print(f"\nIndustry distribution (top 20):")
for ind, count in industry_dist.most_common(20):
    print(f"  {ind}: {count}")

# --- Build pairs ---
# Strategy 1: Same brand, different CTR tier
brand_groups = {}
for ad in ads:
    b = ad["brand_name"]
    if b:
        brand_groups.setdefault(b, []).append(ad)

brand_pairs = []
for brand, group in brand_groups.items():
    if len(group) < 2:
        continue
    group.sort(key=lambda x: x["ctr_percentile"])
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            a, b = group[i], group[j]
            if a["ctr_percentile"] != b["ctr_percentile"]:
                brand_pairs.append({
                    "pair_type": "same_brand",
                    "brand": brand,
                    "industry": a["industry"],
                    "ad_a_id": a["id"],
                    "ad_a_text": a["ad_title"],
                    "ad_a_ctr_pct": a["ctr_percentile"],
                    "ad_a_ctr_label": a["ctr_readable"],
                    "ad_a_likes": a["likes"],
                    "ad_b_id": b["id"],
                    "ad_b_text": b["ad_title"],
                    "ad_b_ctr_pct": b["ctr_percentile"],
                    "ad_b_ctr_label": b["ctr_readable"],
                    "ad_b_likes": b["likes"],
                    "winner_ground_truth": "A",
                    "ctr_gap": abs(b["ctr_percentile"] - a["ctr_percentile"]),
                })

print(f"\nBrand-based pairs (same brand, different CTR): {len(brand_pairs)}")

# Strategy 2: Same industry, different CTR tier (random sampling)
import random
random.seed(42)

industry_groups = {}
for ad in ads:
    ind = ad["industry"]
    if ind:
        industry_groups.setdefault(ind, []).append(ad)

industry_pairs = []
for ind, group in industry_groups.items():
    if len(group) < 2:
        continue
    # Sort by CTR percentile
    group.sort(key=lambda x: x["ctr_percentile"])
    # Take pairs from different CTR tiers (top quartile vs bottom quartile)
    n = len(group)
    top_quarter = group[:max(1, n // 4)]
    bottom_quarter = group[max(1, 3 * n // 4):]
    if not bottom_quarter:
        bottom_quarter = group[n // 2:]

    sampled = 0
    for top_ad in top_quarter:
        for bot_ad in bottom_quarter:
            if top_ad["id"] == bot_ad["id"]:
                continue
            if top_ad["ctr_percentile"] == bot_ad["ctr_percentile"]:
                continue
            industry_pairs.append({
                "pair_type": "same_industry",
                "brand": f"{ind}",
                "industry": ind,
                "ad_a_id": top_ad["id"],
                "ad_a_text": top_ad["ad_title"],
                "ad_a_ctr_pct": top_ad["ctr_percentile"],
                "ad_a_ctr_label": top_ad["ctr_readable"],
                "ad_a_likes": top_ad["likes"],
                "ad_b_id": bot_ad["id"],
                "ad_b_text": bot_ad["ad_title"],
                "ad_b_ctr_pct": bot_ad["ctr_percentile"],
                "ad_b_ctr_label": bot_ad["ctr_readable"],
                "ad_b_likes": bot_ad["likes"],
                "winner_ground_truth": "A",
                "ctr_gap": abs(bot_ad["ctr_percentile"] - top_ad["ctr_percentile"]),
            })
            sampled += 1
            if sampled >= 5:
                break
        if sampled >= 5:
            break

print(f"Industry-based pairs (same industry, different CTR): {len(industry_pairs)}")

# Combine and deduplicate
all_pairs = brand_pairs + industry_pairs
# Deduplicate by pair of IDs
seen_pair_ids = set()
unique_pairs = []
for p in all_pairs:
    key = tuple(sorted([p["ad_a_id"], p["ad_b_id"]]))
    if key not in seen_pair_ids:
        seen_pair_ids.add(key)
        unique_pairs.append(p)

# Label decisive vs close
for p in unique_pairs:
    p["is_decisive"] = p["ctr_gap"] >= 0.10

decisive = sum(1 for p in unique_pairs if p["is_decisive"])
close = len(unique_pairs) - decisive
print(f"\nTotal unique pairs: {len(unique_pairs)}")
print(f"  Decisive (CTR gap >= 10pp): {decisive}")
print(f"  Close race (CTR gap < 10pp): {close}")

# Write all ads
ads_path = os.path.join(OUT_DIR, "tiktok_ads_clean.csv")
with open(ads_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "ad_title", "brand_name", "likes", "ctr_percentile",
        "ctr_readable", "industry", "objective", "video_duration"
    ])
    writer.writeheader()
    for ad in ads:
        writer.writerow(ad)
print(f"\nSaved {len(ads)} clean ads to {ads_path}")

# Write pairs
pairs_path = os.path.join(OUT_DIR, "validation_pairs.csv")
pair_fields = [
    "pair_type", "brand", "industry",
    "ad_a_id", "ad_a_text", "ad_a_ctr_pct", "ad_a_ctr_label", "ad_a_likes",
    "ad_b_id", "ad_b_text", "ad_b_ctr_pct", "ad_b_ctr_label", "ad_b_likes",
    "winner_ground_truth", "ctr_gap", "is_decisive"
]
with open(pairs_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=pair_fields)
    writer.writeheader()
    for p in unique_pairs:
        writer.writerow(p)
print(f"Saved {len(unique_pairs)} pairs to {pairs_path}")
