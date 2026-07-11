"""
Backtest: run every validation pair through the Marketing Simulation engine
and measure pairwise ranking accuracy against TikTok Creative Center CTR tiers.

Ground truth: Ad A always has the LOWER ctr_percentile (= better CTR tier).
If the simulator gives Ad A a higher score than Ad B, it "agrees" with reality.

Reports overall accuracy, accuracy by gap size, by industry, and by pair type.
"""

import csv
import sys
import os
import time

sys.path.insert(0, "/home/user/Marketing-Simulation")

from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation
from src.agents.agent_generator import generate_population_arrays
import numpy as np

PAIRS_PATH = "/home/user/Marketing-Simulation/validation_data/validation_pairs.csv"
RESULTS_PATH = "/home/user/Marketing-Simulation/validation_data/backtest_results.csv"
REPORT_PATH = "/home/user/Marketing-Simulation/validation_data/VALIDATION_REPORT.md"

NUM_AGENTS = 1000
SEED = 42

print("Generating shared population...")
master_pop = generate_population_arrays(NUM_AGENTS, seed=SEED)

with open(PAIRS_PATH, "r", encoding="utf-8") as f:
    pairs = list(csv.DictReader(f))

print(f"Running backtest on {len(pairs)} pairs with {NUM_AGENTS} agents each...")

results = []
correct = 0
total = 0
correct_decisive = 0
total_decisive = 0
correct_close = 0
total_close = 0

industry_stats = {}
pair_type_stats = {}
gap_bucket_stats = {}

t0 = time.time()

for i, pair in enumerate(pairs):
    ad_a_text = pair["ad_a_text"]
    ad_b_text = pair["ad_b_text"]
    industry = pair["industry"]
    pair_type = pair["pair_type"]
    is_decisive = pair["is_decisive"] == "True"
    ctr_gap = float(pair["ctr_gap"])

    # Bucket the gap
    if ctr_gap < 0.05:
        gap_bucket = "<5pp"
    elif ctr_gap < 0.10:
        gap_bucket = "5-10pp"
    elif ctr_gap < 0.20:
        gap_bucket = "10-20pp"
    elif ctr_gap < 0.30:
        gap_bucket = "20-30pp"
    else:
        gap_bucket = "30pp+"

    # Run Ad A through simulator
    pop_a = {k: v.copy() for k, v in master_pop.items()}
    sim_a = MaxSimulation(seed=SEED, population=pop_a)
    ad_a = Ad(text=ad_a_text, channel='facebook', creative_type='video', price=20.0)
    res_a = sim_a.simulate_exposure(ad_a)
    score_a = res_a.get("conversions", 0)

    # Run Ad B through simulator
    pop_b = {k: v.copy() for k, v in master_pop.items()}
    sim_b = MaxSimulation(seed=SEED, population=pop_b)
    ad_b = Ad(text=ad_b_text, channel='facebook', creative_type='video', price=20.0)
    res_b = sim_b.simulate_exposure(ad_b)
    score_b = res_b.get("conversions", 0)

    # Ground truth: A is always the better ad (lower ctr_percentile = better CTR)
    sim_winner = "A" if score_a > score_b else ("B" if score_b > score_a else "TIE")
    is_correct = sim_winner == "A"

    total += 1
    if is_correct:
        correct += 1

    if is_decisive:
        total_decisive += 1
        if is_correct:
            correct_decisive += 1
    else:
        total_close += 1
        if is_correct:
            correct_close += 1

    # Industry stats
    if industry not in industry_stats:
        industry_stats[industry] = {"correct": 0, "total": 0}
    industry_stats[industry]["total"] += 1
    if is_correct:
        industry_stats[industry]["correct"] += 1

    # Pair type stats
    if pair_type not in pair_type_stats:
        pair_type_stats[pair_type] = {"correct": 0, "total": 0}
    pair_type_stats[pair_type]["total"] += 1
    if is_correct:
        pair_type_stats[pair_type]["correct"] += 1

    # Gap bucket stats
    if gap_bucket not in gap_bucket_stats:
        gap_bucket_stats[gap_bucket] = {"correct": 0, "total": 0}
    gap_bucket_stats[gap_bucket]["total"] += 1
    if is_correct:
        gap_bucket_stats[gap_bucket]["correct"] += 1

    results.append({
        "pair_idx": i,
        "pair_type": pair_type,
        "industry": industry,
        "ad_a_ctr_pct": pair["ad_a_ctr_pct"],
        "ad_b_ctr_pct": pair["ad_b_ctr_pct"],
        "ctr_gap": ctr_gap,
        "is_decisive": is_decisive,
        "sim_score_a": score_a,
        "sim_score_b": score_b,
        "sim_winner": sim_winner,
        "ground_truth": "A",
        "correct": is_correct,
    })

    if (i + 1) % 100 == 0:
        elapsed = time.time() - t0
        acc = correct / total * 100
        print(f"  {i+1}/{len(pairs)} done ({elapsed:.1f}s) — running accuracy: {acc:.1f}%")

elapsed = time.time() - t0
print(f"\nBacktest complete in {elapsed:.1f}s")

# Save detailed results
with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
print(f"Saved detailed results to {RESULTS_PATH}")

# --- Generate report ---
overall_acc = correct / total * 100 if total else 0
decisive_acc = correct_decisive / total_decisive * 100 if total_decisive else 0
close_acc = correct_close / total_close * 100 if total_close else 0

ties = sum(1 for r in results if r["sim_winner"] == "TIE")

report = f"""# Real-World Validation Report — Marketing Simulation Engine

**Date:** 2026-07-11
**Data source:** TikTok Creative Center (Top Ads) via Apify
**Ground truth metric:** CTR percentile tier (TikTok's own ranking)
**Simulation agents:** {NUM_AGENTS} per ad, shared population, seed={SEED}
**Total ads in dataset:** 1,363 (English, valid CTR, text >= 10 chars)
**Total pairs tested:** {total}

---

## HEADLINE RESULT

**Overall pairwise ranking accuracy: {overall_acc:.1f}%**
(Chance = 50%. Statistically significant at p < 0.001 if > ~53% on {total} pairs.)

| Subset | Correct | Total | Accuracy |
|--------|---------|-------|----------|
| **All pairs** | {correct} | {total} | **{overall_acc:.1f}%** |
| Decisive (gap >= 10pp) | {correct_decisive} | {total_decisive} | **{decisive_acc:.1f}%** |
| Close race (gap < 10pp) | {correct_close} | {total_close} | **{close_acc:.1f}%** |
| Ties (simulator couldn't distinguish) | {ties} | {total} | — |

---

## Accuracy by CTR gap size

| Gap bucket | Correct | Total | Accuracy |
|------------|---------|-------|----------|
"""

for bucket in ["<5pp", "5-10pp", "10-20pp", "20-30pp", "30pp+"]:
    s = gap_bucket_stats.get(bucket, {"correct": 0, "total": 0})
    acc = s["correct"] / s["total"] * 100 if s["total"] else 0
    report += f"| {bucket} | {s['correct']} | {s['total']} | {acc:.1f}% |\n"

report += f"""
---

## Accuracy by pair type

| Type | Correct | Total | Accuracy |
|------|---------|-------|----------|
"""

for pt, s in sorted(pair_type_stats.items()):
    acc = s["correct"] / s["total"] * 100 if s["total"] else 0
    report += f"| {pt} | {s['correct']} | {s['total']} | {acc:.1f}% |\n"

report += f"""
---

## Accuracy by industry (top 20 by volume)

| Industry | Correct | Total | Accuracy |
|----------|---------|-------|----------|
"""

sorted_industries = sorted(industry_stats.items(), key=lambda x: -x[1]["total"])
for ind, s in sorted_industries[:20]:
    acc = s["correct"] / s["total"] * 100 if s["total"] else 0
    report += f"| {ind} | {s['correct']} | {s['total']} | {acc:.1f}% |\n"

report += f"""
---

## Honest interpretation

"""

if overall_acc < 52:
    report += """**VERDICT: The simulator is no better than a coin flip.**

The model's pairwise ranking accuracy is statistically indistinguishable from
random (50%). The weights are uncalibrated, and the keyword-based scoring does
not capture what makes an ad perform well on TikTok.

**What this means:** The current engine cannot reliably predict which creative
will outperform another. The "Digital Wind Tunnel" framing is not yet earned.

**Next step:** Fit the simulation weights to this real-world data using
gradient-based optimization. The population + psychology framework is sound;
the weights are wrong.
"""
elif overall_acc < 60:
    report += f"""**VERDICT: Weak but real signal ({overall_acc:.1f}%).**

The simulator picks the real winner slightly more often than chance. There is
a faint signal in the text-based scoring, but it's not strong enough to be
commercially useful on its own.

**What this means:** The architecture works. The keyword scorer captures some
real information. But the weights need calibration against real data.

**Next step:** Use this dataset to optimize the simulation weights. Even a
5-10 percentage point accuracy gain would make this commercially defensible.
"""
elif overall_acc < 70:
    report += f"""**VERDICT: Moderate signal ({overall_acc:.1f}%) — commercially interesting.**

The simulator correctly ranks ad creative performance {overall_acc:.1f}% of the
time on real TikTok data. This is meaningfully above chance and suggests the
text-analysis pipeline captures real creative quality signals.

**What this means:** You have a product that works. Not perfectly, but
measurably better than guessing. This is a defensible claim.

**Next step:** Calibrate weights to push toward 70%+, then build the pitch
deck around this validated number.
"""
else:
    report += f"""**VERDICT: Strong signal ({overall_acc:.1f}%) — this is a real product.**

The simulator correctly predicts the better-performing creative {overall_acc:.1f}%
of the time on real TikTok data. This is a strong, commercially defensible result.

**What this means:** The "Digital Wind Tunnel" framing is earned. This is
better than human intuition for most marketers.

**Next step:** Build the pitch deck around this number. This is the slide
that gets you the meeting.
"""

report += f"""
---

## Methodology notes

1. **Data source:** 1,363 real TikTok ads scraped from TikTok Creative Center
   (the official ad intelligence tool) via Apify. Ads span 12+ industries,
   US + UK markets, English language, last 180 days.

2. **CTR ground truth:** TikTok Creative Center provides CTR percentile tiers
   (e.g., "Top 1%", "Top 20%"). These represent real advertiser click-through
   performance, not proxy metrics. Lower percentile = better performance.

3. **Pairing strategy:** Pairs were created two ways:
   - **Same-brand pairs** ({pair_type_stats.get('same_brand', {}).get('total', 0)} pairs):
     two ads from the same advertiser with different CTR tiers.
   - **Same-industry pairs** ({pair_type_stats.get('same_industry', {}).get('total', 0)} pairs):
     two ads from the same industry vertical with different CTR tiers.

4. **Simulation:** Each ad's text was scored by the engine's keyword + neural
   scorer pipeline, then run through the population simulation (1,000 agents,
   shared population, fixed seed) to produce a conversion count. The ad with
   more simulated conversions was the simulator's "pick."

5. **Limitation:** The simulator scores TEXT only. TikTok ads are primarily
   video — the visual creative likely drives a large portion of CTR variance
   that text analysis cannot capture. A text-only accuracy of {overall_acc:.1f}%
   on a video-dominated platform is {"surprisingly strong" if overall_acc > 55 else "expected to be limited"}.
"""

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(report)
print(f"\nValidation report saved to {REPORT_PATH}")

# Print summary
print(f"\n{'='*60}")
print(f"OVERALL PAIRWISE ACCURACY: {overall_acc:.1f}%")
print(f"  Decisive pairs: {decisive_acc:.1f}%")
print(f"  Close races:    {close_acc:.1f}%")
print(f"  Ties:           {ties}/{total}")
print(f"{'='*60}")
