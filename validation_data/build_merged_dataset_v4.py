"""
Merge THREE scrape waves (wave1 2026-07-11, wave2 2026-07-12 morning,
wave3 2026-07-12 afternoon/ecommerce-targeted) into one corpus and re-split
by brand-hash across the combined pool -- same protocol as
build_merged_dataset.py (the v4->v5 fix), extended to a third wave.
"""
import csv
import hashlib
import random
from collections import Counter

random.seed(3)

with open("/home/user/Marketing-Simulation/validation_data/tiktok_ads_clean.csv", encoding="utf-8") as f:
    wave1 = list(csv.DictReader(f))
with open("/home/user/Marketing-Simulation/validation_data/fresh_ads_clean.csv", encoding="utf-8") as f:
    wave2 = list(csv.DictReader(f))
with open("/home/user/Marketing-Simulation/validation_data/wave3_ads_clean.csv", encoding="utf-8") as f:
    wave3 = list(csv.DictReader(f))
with open("/home/user/Marketing-Simulation/validation_data/wave4_ads_clean.csv", encoding="utf-8") as f:
    wave4 = list(csv.DictReader(f))

for a in wave1:
    a["wave"] = "wave1_20260711"
for a in wave2:
    a["wave"] = "wave2_20260712"
# wave3 already tagged wave3_20260712 in build_wave3.py

by_id = {}
for a in wave1 + wave2 + wave3 + wave4:
    by_id[a["id"]] = a

ads = list(by_id.values())
print(f"Merged unique ads: {len(ads)} (w1={len(wave1)}, w2={len(wave2)}, w3={len(wave3)}, w4={len(wave4)})")


def norm_text(t):
    return " ".join((t or "").lower().split())


# --- De-duplicate by normalized ad text (leakage fix) --------------------
# Keyword search returns the SAME ad copy under many different ad IDs (often
# with blank brand names). If those copies scatter across train/holdout the
# model memorizes text->CTR and holdout accuracy is inflated. Keep exactly
# one ad per normalized text (prefer a branded, higher-info copy), so no
# identical text can ever straddle the split.
by_text = {}
for a in ads:
    key = norm_text(a["ad_title"])
    cur = by_text.get(key)
    if cur is None:
        by_text[key] = a
    else:
        # prefer the one with a real brand name; tie-break: keep existing
        if not cur["brand_name"].strip() and a["brand_name"].strip():
            by_text[key] = a
before = len(ads)
ads = list(by_text.values())
print(f"After exact-text dedup: {len(ads)} ads (removed {before - len(ads)} duplicate-copy ads)")


def bucket_of_ad(ad):
    # Split key = brand when known, else the normalized TEXT (not the ad id).
    # This keeps same-brand pairs within one split AND keeps any residual
    # identical/near-identical blank-brand copies from crossing the split.
    group = ad["brand_name"].strip().lower() or f"txt::{norm_text(ad['ad_title'])}"
    h = int(hashlib.md5(group.encode()).hexdigest(), 16) % 100
    return "train" if h < 60 else ("val" if h < 80 else "holdout")


for ad in ads:
    ad["split"] = bucket_of_ad(ad)

split_wave = Counter((a["split"], a["wave"]) for a in ads)
print("Split x wave distribution:")
for k, v in sorted(split_wave.items()):
    print(f"  {k}: {v}")


def make_pair(a, b, pair_type):
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
        "ctr_gap": round(abs(float(b["ctr_percentile"]) - float(a["ctr_percentile"])), 4),
    }


ctr = lambda a: float(a["ctr_percentile"])

brand_groups = {}
for ad in ads:
    if ad["brand_name"]:
        brand_groups.setdefault(ad["brand_name"], []).append(ad)

brand_pairs = []
for brand, group in brand_groups.items():
    group.sort(key=ctr)
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            a, b = group[i], group[j]
            if ctr(a) != ctr(b) and a["ad_title"].strip() != b["ad_title"].strip() \
                    and a["split"] == b["split"]:
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
    for _ in range(min(400, n * 4)):
        a = random.choice(group)
        b = random.choice(group)
        if a["id"] == b["id"] or ctr(a) == ctr(b):
            continue
        if a["ad_title"].strip() == b["ad_title"].strip():
            continue
        if a["split"] != b["split"]:
            continue
        if ctr(a) > ctr(b):
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
print(f"\nTotal unique merged pairs: {len(unique_pairs)}")
print(f"  Decisive (gap >= 10pp): {decisive}")

split_pairs = Counter(p["split"] for p in unique_pairs)
print(f"Pairs by split: {dict(split_pairs)}")

OUT_DIR = "/home/user/Marketing-Simulation/validation_data"
ads_path = f"{OUT_DIR}/merged_ads_clean.csv"
with open(ads_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "ad_title", "brand_name", "likes", "ctr_percentile",
        "ctr_readable", "industry", "objective", "video_duration",
        "video_cover", "video_url_720p", "split", "wave",
    ])
    writer.writeheader()
    writer.writerows(ads)
print(f"\nSaved {len(ads)} ads -> {ads_path}")

pairs_path = f"{OUT_DIR}/merged_validation_pairs.csv"
with open(pairs_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(unique_pairs[0].keys()))
    writer.writeheader()
    writer.writerows(unique_pairs)
print(f"Saved {len(unique_pairs)} pairs -> {pairs_path}")
