# Real-World Validation — Creative Ranker v2 (Deployable Mode)

**Date:** 2026-07-11
**Ground truth:** TikTok Creative Center CTR percentile tiers (real advertiser
outcomes), scraped via Apify across US/GB/CA/AU/IE/NZ, 7/30/180-day windows.
**Dataset:** 2,489 unique English ads → 3,211 pairs (2,044 decisive).
**Visual ground truth:** 1,374 real ad cover thumbnails, featurized and
trained against the same CTR tiers.

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

## Reproduce

```bash
python3 validation_data/build_validation_dataset.py   # rebuild pairs from scrapes
python3 validation_data/download_thumbnails.py        # visual ground truth
python3 validation_data/train_ranker.py               # train + holdout eval
python3 validation_data/e2e_backtest.py               # end-to-end app-path test
```

Model artifact: `models/creative_ranker.joblib` (loaded by
`src/ai/creative_ranker.py`; the app integrates it in
`src/simulation/ab_test_runner.py` and surfaces confidence in `app.py`).
