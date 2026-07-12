# Real-World Validation — Creative Ranker

**Current shipped version: v7 (2026-07-12).** Trained on a 4-wave corpus of
12,992 leakage-deduplicated real TikTok ecommerce ads. **Read the "v7 honest
reckoning" section immediately below before quoting any number — v7 corrected
two methodology bugs (text leakage and a train/deploy calibration mismatch)
that were inflating every earlier version's figures, including v5 and v6.**

## The v7 honest reckoning (2026-07-12) — READ FIRST

A $40 scrape (8 Apify keys × 275 ecommerce keywords) added **11,950 new unique
English ecommerce ads**, growing the corpus ~5× to 15,008 ads. In processing
it, two bugs were found that had been quietly inflating results since v5:

1. **Text leakage across the train/holdout split.** Keyword search returns the
   *same ad copy* under many different ad IDs, usually with blank brand names.
   The brand-hash split scattered those identical copies across train and
   holdout, so the model was partly memorizing text→CTR. Measured leakage:
   **18.7% of the 4-wave holdout pairs** (and **10.2% of v6's 3-wave holdout**)
   had an ad text also present in training. Fix: exact-text dedup (15,008 →
   12,992 ads) + split key = brand-else-normalized-text. Post-fix leakage: **0%**.

2. **Train/deploy calibration mismatch.** The trainer tuned the abstention
   threshold on isotonic-calibrated confidence, but the shipped `compare()`
   path gates on **raw** probability and never applied the calibrator. On the
   larger corpus the isotonic step became degenerate (collapsing points to a
   few plateaus → fake 95%+ "confidence"). Fix: dropped isotonic, tune and
   deploy on the same raw confidence.

**What the honest, leakage-free numbers actually are (v7, 1,112-pair holdout):**
- **Ungated accuracy: ~55%.** Every model class (logistic, gradient-boosted,
  ensemble) plateaus at ~52–53% on validation. This is a **data/label ceiling,
  not a model ceiling** — TikTok Creative Center CTR *percentile tiers* reflect
  targeting, budget, audience and timing far more than ad copy, so text (+
  thumbnail) features can only predict them slightly better than chance.
- **Confidence gating helps but is not stable enough to certify 75%.** The
  accuracy/call-rate curve looks clean on the holdout split (e.g. threshold
  0.68 → 75.7% at 15% call rate) but the **validation split disagrees sharply
  at the same thresholds** (0.68 → 56.5%). The two splits only *agree* at the
  very top of the confidence range (threshold ~0.80): pooled val+holdout there
  is **81.8% (n=22, 95% CI 61.5–92.7%)** at a **~2–3% call rate**.

**Bottom line for selling to ecommerce businesses:** the earlier "80.6% on
called pairs" (v6) and "82.8%" (v4) figures were **inflated by text leakage
plus small-sample gating luck** and should not be quoted. The honest state is:
the model ranks ad copy *slightly* better than chance overall (~55%), and on
the ~2–3% of comparisons where it is most confident it is preliminarily ~80%
accurate (small n, wide CI). **A reliable, certified "75% on all ecommerce
ads" is NOT achievable from TikTok CTR-tier data with text/thumbnail features**
— this was proven, not assumed, across four scrape waves and ~13k real ads.
What would move it: outcome labels that actually depend on the creative (real
A/B test lift from customers' own campaigns, or click data tied to specific
creatives), not more Creative-Center CTR tiers. v7 ships at the conservative
threshold 0.80 (abstains unless genuinely confident) and the UI states this
honestly.

---

## (Superseded) v6 ecommerce readiness claim — was leakage-inflated

The v6 section below reported **80.6% on called pairs (n=62)**. Per the v7
reckoning above, v6's holdout had 10.2% text leakage and the calibration
mismatch, so this figure is an overstatement and is retained only for the
historical record. Do not quote it.

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

## The ecommerce specialization attempt (2026-07-12)

**Goal:** get to a defensible 75%+ accuracy floor specifically on ecommerce
ads (Skincare, Apparel, Cosmetics, Haircare, Jewelry, Home Decor, Pet,
Beauty, etc.), so the app could be honestly sold to ecommerce businesses.

**What was available:** 1,497 real ecommerce ads / 1,846 pairs (194 in
holdout, 154 in val) already inside the existing two-wave TikTok Creative
Center corpus — filtered by industry, no new scraping needed for this part.
**What was NOT available:** `APIFY_TOKEN` was not present in this session's
environment, so no fresh scraping was possible. Every result below is from
the existing corpus only.

**Attempt 1 — train an ecommerce-only model from scratch.** Retrained the
full pipeline (embeddings, PCA, HGB ensemble, isotonic calibration) using
only the 1,498 ecommerce training pairs instead of the full 2,887-pair mixed
corpus. Result: **worse, not better** — 62.4% ungated accuracy on the
ecommerce holdout (vs 69.6% for the mixed-industry v5 model on its full
holdout), same-brand accuracy fell to 49.2% (chance), and the confidence
threshold selected on the small ecommerce val set (n=154) badly overfit —
84% call rate at only 61.8% holdout accuracy. **Conclusion: 1,498 pairs is
not enough training data for this feature space; the "irrelevant" industries
in the mixed corpus were providing useful signal, not just noise.**

**Attempt 2 — keep v5's model, re-tune only the confidence threshold on
ecommerce validation data.** This isolates "does the model need
retraining" (no) from "does the abstention cutoff need retuning for this
vertical." Offline, scoring the shipped v5 model directly on the 194-pair
ecommerce holdout at *its own* threshold (0.72) gave a promising 83.3% (n=36,
95% CI 66.1–89.2%). Retuning the threshold down to 0.65 using ecommerce val
data raised the call rate to 23.2% (n=45) at a statistically indistinguishable
80.0% (95% CI 66.2–89.1%).

**The real test — same 194 pairs through the actual `ABTestRunner` app path**
(randomized position, visual features wired in, exactly what a customer's
session does), using the ecommerce-tuned threshold:

- Confident calls: 44/194 (22.7%)
- **Accuracy on called: 70.5%** (95% CI 55.8–81.8%, n=44) — below offline estimate
- Decisive + called: 76.5% (n=34)
- **Same-brand + called: 0/5 correct** — the model's rare same-brand calls were wrong every time

**Decision at that point: did not ship.** Reasons: (1) the real app-path
number missed the 75% target and its CI spanned 56–82%, too wide to defend;
(2) same-brand pairs — the core product use case — were both rarely called
and wrong when they were; (3) the gain over v5's un-tuned threshold wasn't
statistically distinguishable from noise at that sample size.
`models/creative_ranker.joblib` (v5) was left shipped unchanged, and the
identified fix was: **get more ecommerce data, especially same-brand pairs.**

## The v6 rescrape (2026-07-12, same day) — this is what closed the gap

The user supplied a live `APIFY_TOKEN` specifically to fix the data
bottleneck above. 24 varied `top_ads` queries (period × orderBy × country
combinations, chosen to minimize overlap with the existing 2,774-ad corpus)
were run against the same TikTok Creative Center actor
(`rFFzT2mRuOd1K4iTM`), stopping automatically at $4.50 of the account's $5
monthly cap. 12 of 24 queries succeeded (the other 12 all used one
particular country-code combination that the actor rejected — a config
issue, not a budget one); **3,071 raw items came back, of which only 284
were genuinely new** (91% overlapped the existing corpus or failed the
English/valid-CTR filter) — consistent with the leaderboard-saturation
problem already flagged in the v4→v5 section. 175 of the 284 new ads were
ecommerce-industry.

**A data-quality bug was caught before training:** two "brand names" in the
new batch — `"Shopee Brands Festival"` (84 ads) and `"Celebrate 12.12 with
Shopee"` (70 ads) — are platform-wide promotional campaign labels covering
many unrelated sellers, not single advertisers. Pairing within them as
"same-brand" would have taught the model that unrelated brands' ads are
comparable variants, exactly backwards from the real use case. Both were
blanked to empty brand names (so the ads still contribute to same-industry
pairs, just not same-brand ones) before rebuilding the pair set — this
dropped a spurious 5,928 "same-brand" pairs that would have silently
corrupted training.

**Merged 3-wave corpus:** 3,058 ads (wave1: 2,489, wave2: 285, wave3: 284),
3,710 pairs, re-split by brand-hash across all three waves (same anti-
overfitting protocol as v4→v5). Retrained from scratch
(`validation_data/train_ranker_v6.py`) — the model selected on validation
was plain L2-regularized logistic regression (`logreg_C0.1`), not the
gradient-boosted ensemble v5 used.

**Offline holdout (393 pairs, mixed industries):** 77.5% accuracy on called
(n=102, 26.0% call rate), same-brand+called 72.7% (n=33) — both large jumps
from v5's same-brand performance.

**Ecommerce holdout (215 pairs) through the real `ABTestRunner` app path**
(the number that matters — offline consistently overstates real performance
in this project's history):

| Threshold | Call rate | Accuracy on called | 95% CI | Same-brand+called |
|---|---|---|---|---|
| v6 native (0.68, tuned on general val) | 28.8% (n=62) | **80.6%** | 69.1–88.6% | 70.6% (n=17) |
| Ecommerce-retuned (0.57, tuned on ecom val) | 50.2% (n=108) | 75.9% | 67.1–83.0% | 63.4% (n=41) |

**Shipped: v6 at its native 0.68 threshold** — better point accuracy, better
CI floor, and same-brand performance no longer broken. This is a genuine
improvement over the pre-rescrape state (0/5 same-brand correct, 70.5%
overall) and clears the 75% point-estimate target. The ecommerce-retuned
0.57 threshold was evaluated and rejected as the default: it trades accuracy
and CI floor for call rate, and 0.68 dominates it on both accuracy axes.

**Still honestly true, even after this fix:**
- **The CI lower bound (69.1%) is still below 75%.** At n=62 called pairs,
  "80.6% accurate" is a real, current, best-available estimate — not a
  contractual guarantee. Communicate it as "80% in our validation, 95%
  confidence range 69–89%," not as a flat "80% accurate" claim.
- **Same-brand n=17 is still a small sample.** 70.6% is a big improvement
  over 0/5, but 17 called pairs is not enough to rule out regression to
  something closer to the overall same-brand holdout rate (55.6%, n=144,
  offline ungated).
- **Leaderboard saturation is a hard ceiling on this data source.** Only
  284/3,071 raw items were new this round. Another rescrape from the same
  actor with the same query strategy will likely yield diminishing returns;
  a materially larger next wave needs either a different actor/data source
  (e.g. the EU Ads Transparency Library mode, which lacks CTR ground truth)
  or TikTok Creative Center's keyword/search mode explored more
  systematically (it returns smaller but more targeted batches with mostly
  blank brand names, per this session's testing — useful for industry
  coverage, not for same-brand pairs).
- **Still TikTok-only, still Creative Center-only.** No claim is made about
  Meta/Google/email ecommerce creatives, and no real DTC/Shopify business
  data has been incorporated — see the original limitations list above,
  which still applies in full.

Reproduce: `validation_data/scrape_ecom_wave.py` (needs `APIFY_TOKEN`) →
`validation_data/build_wave3.py` → `validation_data/build_merged_dataset_v3.py`
→ `validation_data/train_ranker_v6.py` → `validation_data/build_ecommerce_dataset.py`
→ `validation_data/e2e_backtest_v6_native.py` (real app-path number above).
Earlier, superseded attempt: `validation_data/train_ranker_ecom.py`
(ecommerce-only from-scratch training, negative result) /
`validation_data/retune_threshold_ecom.py` (threshold-only retune, the
0.57-threshold row in the table above).

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
