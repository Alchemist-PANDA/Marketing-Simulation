"""
Map the Upworthy Research Archive into the common A/B-outcome schema, then
build within-test, creative-dependent, significance-filtered pairs.

Upworthy columns -> schema:
  clickability_test_id -> test_id   (arms in one test share audience/window)
  headline             -> creative_text
  impressions, clicks  -> impressions, clicks
  source               -> "upworthy"

Honest note: Upworthy = viral-news headlines (2013-2015), NOT ecommerce ad
copy. This is a PRETRAINING/proof source: it proves the pipeline learns a
real, creative-dependent "what makes text more clickable" signal that the
TikTok CTR-tier data could not provide. Domain transfer to ecommerce is
partial; the target is to fine-tune on the user's own ecommerce A/B exports
through this same schema.
"""
import csv
import os
import sys

sys.path.insert(0, "/home/user/Marketing-Simulation")
from src.ai.outcomes.ab_outcome_schema import Arm, build_pairs, summarize

RAW = "/home/user/Marketing-Simulation/validation_data/outcomes/upworthy_exploratory.csv"
OUT_ARMS = "/home/user/Marketing-Simulation/validation_data/outcomes/upworthy_arms.csv"
OUT_PAIRS = "/home/user/Marketing-Simulation/validation_data/outcomes/upworthy_pairs.csv"

csv.field_size_limit(10_000_000)

arms = []
with open(RAW, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        hl = (r.get("headline") or "").strip()
        if not hl:
            continue
        try:
            imp = int(float(r["impressions"])); clk = int(float(r["clicks"]))
        except (ValueError, TypeError, KeyError):
            continue
        if imp <= 0:
            continue
        arms.append(Arm(
            test_id=(r.get("clickability_test_id") or "").strip(),
            creative_text=hl, impressions=imp, clicks=clk, source="upworthy",
        ))

print(f"Loaded {len(arms)} arms")
pairs = build_pairs(arms, objective="clicks", min_impressions=500,
                    require_significant=True, max_pairs_per_test=6,
                    drop_identical_text=True)
print("Summary:", summarize(arms, pairs))

# assign a leakage-safe split by TEST id (a whole test goes to one split, so
# no arm of a test can leak across train/holdout)
import hashlib


def split_of(tid):
    h = int(hashlib.md5(tid.encode()).hexdigest(), 16) % 100
    return "train" if h < 70 else ("val" if h < 85 else "holdout")


with open(OUT_ARMS, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["test_id", "creative_id", "creative_text", "impressions",
                "clicks", "rate", "source", "split"])
    for a in arms:
        w.writerow([a.test_id, a.creative_id, a.creative_text, a.impressions,
                    a.clicks, f"{a.rate():.6f}", a.source, split_of(a.test_id)])

with open(OUT_PAIRS, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["test_id", "split", "ad_a_id", "ad_a_text", "ad_b_id",
                "ad_b_text", "rate_a", "rate_b", "rate_gap", "n_a", "n_b",
                "is_decisive", "pair_type", "ctr_gap", "source"])
    for p in pairs:
        dec = p.rate_gap >= 0.02  # 2pp click-rate gap
        w.writerow([p.test_id, split_of(p.test_id), p.a.creative_id,
                    p.a.creative_text, p.b.creative_id, p.b.creative_text,
                    f"{p.rate_a:.6f}", f"{p.rate_b:.6f}", f"{p.rate_gap:.6f}",
                    p.n_a, p.n_b, dec, "within_test", f"{p.rate_gap:.6f}",
                    p.source])

from collections import Counter
sp = Counter(split_of(p.test_id) for p in pairs)
print(f"Pairs by split: {dict(sp)}")
print(f"Saved -> {OUT_ARMS}, {OUT_PAIRS}")
