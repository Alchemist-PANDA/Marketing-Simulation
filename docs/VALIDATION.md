# Real-World Validation — Creative Ranker

**Current shipped version: v5 (2026-07-12).** v4's numbers below turned out to
be overfit to a single scrape wave — see "The v4 → v5 correction" for the
full honest account of how that was discovered and fixed.

**Ground truth:** TikTok Creative Center CTR percentile tiers (real advertiser
outcomes), scraped via Apify across US/GB/CA/AU/IE/NZ, 7/30/180-day windows.
**Dataset (v5):** 2,774 unique English ads from **two separate scrape waves**
(2,489 from 2026-07-11, 285 from 2026-07-12) → 3,520 pairs (2,281 decisive).
**Visual ground truth:** 1,659 real ad cover thumbnails, featurized and
trained against the same CTR tiers.

## The v4 → v5 correction (read this first)

v4 was trained and holdout-evaluated on ads from a **single scrape wave**
(one 7-day window), with brand-hash splitting only. It reported 82.8%
end-to-end accuracy on confident calls. When tested against 285 genuinely
new ads scraped a day later (never seen in training, zero retraining), it
collapsed to **49.7% ungated accuracy (n=547, 95% CI 45.6–53.9%)** —
statistically indistinguishable from chance, despite the fresh pairs having
a nearly identical CTR-gap distribution to the original holdout. The model
had learned wave-specific artifacts, not durable ad-quality signal.

**Fix:** merged both waves into one corpus (2,774 ads) and re-split by
brand-hash across the *combined* pool, so both train and holdout now contain
ads from both scrape dates. Retrained with the same deployable-mode protocol
(no objective/industry features, averaged-both-orderings evaluation).

**Result (v5, holdout spans both waves, through the real ABTestRunner app path):**
- Confident calls: 43/355 (12.1% call rate)
- **Accuracy on called: 69.8%** (95% CI 54.9–81.4%, n=43)
- **Decisive + called: 80.8%** (95% CI 62.1–91.5%, n=26)

This is centered at the 70% target but the confidence interval is wide — n=43
called pairs isn't huge. It is a real, methodologically honest improvement
over v4's wave-specific overfit, not a guaranteed 70%+ in all conditions.

**What we could NOT do:** get a third, fully independent scrape wave for a
true blind test. The scraper's "top ads" leaderboard mode is heavily
saturated — re-querying with different orderings (cvr, impression),
periods, and start dates against the same country set returned largely the
same ~126 ads each time (only 9 were genuinely new after two more scrape
attempts). The `library`/keyword-search mode exists but returned 0 results
for the query tried, and the remaining Apify budget ($1.25 of the original
$5) wasn't enough to responsibly keep exploring query combinations. This is
flagged, not hidden: the 69.8% figure is validated across two waves, not
three, and should be treated as directionally strong rather than final.

---

# v4 numbers (superseded, kept for the historical record)

---

## The journey (all numbers on untouched holdout data)

| Stage | Overall | Decisive | Called pairs |
|---|---|---|---|
| v0: keyword scorer + hand weights | **26.0%** | 33.7% | — (no confidence system) |
| v0 diagnosis | 48% ties; non-tie subset exactly 50/50 (pure noise) | | |
| v3: learned ranker + context features | 65.2% | 70.5% | 74.4% |
| v3 through real app path | — | — | 60.9% ← **offline metric was inflated** |
| **v4: deployable mode + visual features** | **69.6%** | **79.0%** | **81.4%** |
| **v4 through real app path (end-to-end)** | — | — | **82.8%** (87.5% decisive) |

## Final holdout numbers (v4, the shipped model)

- **All 273 holdout pairs:** 69.6%
- **Same-brand pairs** (hardest, most product-like): 67.7%
- **Decisive pairs (CTR gap ≥ 10pp):** 79.0%
- **Large gaps (30pp+):** 85.2%
- **Confidence-gated calls:** 81.4% accuracy (15.8% call rate)
- **Decisive + called:** 90.6%
- **End-to-end through ABTestRunner** (randomized positions, visual features
  active): **82.8% on called, 87.5% on decisive+called**

## What made the difference

1. **Killing the keyword scorer as decision-maker.** It had literally zero
   signal on real data (50.1% on non-tie pairs).
2. **Learning from real outcomes.** Pairwise ranker (HistGradientBoosting on
   PCA-64 MiniLM embeddings + 22 copy features), trained on 2,620 pairs.
3. **Deployable-mode honesty.** v3 scored 84.6% offline using objective/
   industry features — but those cancel out when a user compares two
   creatives for the same campaign, and the real app path scored only ~61%.
   v4 trains ONLY on features the app truly has. Its offline metric IS the
   deployed metric (81.4% offline vs 82.8% end-to-end — consistent).
4. **Visual features trained on real thumbnails.** Brightness, contrast,
   colorfulness, edge density, aspect ratio from 1,374 real ad covers.
   This lifted same-brand pairs from 55.9% → 67.7% — the visual creative
   carries signal the caption can't.
5. **Calibrated confidence + abstention.** Isotonic calibration on the
   validation set; the model only "calls" a winner at ≥72% calibrated
   confidence. Below that the product says "too close to call — test both,"
   which is the honest answer on coin-flip pairs.

## Honest limitations (read before quoting numbers)

- **The call rate is deliberately low (~11–16%).** The model abstains on
  most close races. The 80%+ number applies to the calls it makes, exactly
  like a weather forecaster's "confident" days. Marketing claims must say
  "82.8% accurate on confident calls" — never "82.8% accurate."
- **Same-brand called sample is tiny** (n=2 in holdout) — not enough to
  quote a same-brand called accuracy yet. More data needed.
- **CTR tiers are noisy labels.** Pairs under 5pp apart are near-random for
  any model (we scored 58.2% there; ceiling is ~60%).
- **Ground truth is TikTok.** Accuracy on Meta/Google/e-mail creatives is
  unmeasured. The text model likely transfers partially; claims should stay
  platform-scoped until cross-platform data is collected.
- **Video features (motion, hook strength, cut rate) are heuristic** — the
  trained visual features are from static thumbnails. Training temporal
  features against outcomes needs video downloads (next milestone).

## Reproduce (v5, current)

```bash
python3 validation_data/build_merged_dataset.py   # merge waves, wave-diverse split
python3 validation_data/train_ranker_v5.py        # train + offline holdout eval
python3 validation_data/e2e_backtest_v5.py         # end-to-end app-path test (temporarily
                                                    # point models/creative_ranker.joblib at
                                                    # the candidate before running)
```

Model artifact: `models/creative_ranker.joblib` (loaded by
`src/ai/creative_ranker.py`; the app integrates it in
`src/simulation/ab_test_runner.py` and surfaces confidence in `app.py`).
Previous version kept at `models/creative_ranker_v4_backup.joblib` for
rollback/comparison.

## Data lake (pretraining corpus, not yet integrated into the ranker)

`/home/user/datalake/` (session-local, not committed to git — see its
`README.md`) holds 330k+ real rows from Criteo 1TB Click Logs, Criteo
Kaggle-lineage CTR, Avazu, iPinYou RTB, and Taobao ad-behavior logs, plus
the merged TikTok creative hub. These are stored as **independent
pretraining satellites** — anonymized/hashed features with zero ID overlap
to the creative hub, deliberately never joined row-to-row with it. They are
not yet used in the ranker; using them would require training a separate
CTR encoder on them and transferring the learned weights, which is future
work, not something this session claims to have done.
