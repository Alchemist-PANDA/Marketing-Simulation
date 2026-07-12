# Outcome-Based Training — the real path to 75% on ecommerce

This is the Option-A pipeline: train the creative ranker on labels that
**depend on the creative** (real A/B test results), instead of TikTok
Creative-Center CTR percentile tiers.

## Why this exists (the core finding)

`docs/VALIDATION.md` proved, across 4 scrape waves and ~13,000 real TikTok
ads, that CTR *percentile tiers* are only ~55% predictable from ad text — a
**data/label ceiling**, because those tiers are driven mostly by targeting,
budget, audience and timing, not the creative. No amount of model tuning or
extra TikTok scraping moved it.

The fix is a different **label**, not a different model. Within a single A/B
test, every variant is shown to the *same* audience over the *same* window,
so the difference in click/conversion rate between two variants isolates the
causal effect of the creative. Train on those within-test pairs and the text
suddenly carries real, learnable signal.

## Proof it works (Upworthy Research Archive)

The [Upworthy Research Archive](https://osf.io/jd64p/) is 32,487 real headline
A/B tests (impressions + clicks per variant). We ingested the 4,873-experiment
exploratory set through this pipeline (within-test pairs, 2-proportion
significance filter, split by test id so no variant leaks across train/holdout):

| | Call rate | Accuracy | 95% CI |
|---|---|---|---|
| Ungated | 100% | **69.1%** | 66.1–71.8 |
| Confidence ≥ 0.65 | 70% | **74.0%** | 70.6–77.1 |
| Confidence ≥ 0.70 | 60% | **75.3%** | 71.7–78.6 |
| Confidence ≥ 0.75 | 50% | **78.1%** | 74.3–81.5 |

Compare to ~55% ungated / 2–3% usable call-rate on TikTok CTR tiers. The
confidence gating is **stable and monotonic** on a 1,005-pair holdout. This
is the target behavior: **75%+ at a practical 50–60% call rate.**

**Honest caveat — domain gap.** Upworthy is viral-news headlines (2013–2015),
not ecommerce product ads. The Upworthy-trained model scores only ~55% on the
TikTok ecommerce holdout — but that holdout's *labels* are the near-noise CTR
tiers, so that number reflects the bad labels, not necessarily bad transfer.
Upworthy is therefore a **proof-of-concept and pretraining base**, not the
shipped ecommerce model. It demonstrates the pipeline learns genuine
"clickability" signal; ecommerce-specific accuracy requires ecommerce A/B data.

## The input schema (bring your own data)

One CSV row per creative variant (`src/ai/outcomes/ab_outcome_schema.py`).
See `validation_data/outcomes/TEMPLATE_ab_outcomes.csv` for a filled example.

Required columns:
- `test_id` — groups variants tested against each other (same audience/window)
- `creative_text` — the ad copy / headline
- `impressions` — how many saw this variant (> 0)
- `clicks` — how many clicked (use `conversions` column for a conversion test)

Optional (used if present): `conversions`, `creative_id`, `image_path`,
`video_path`, `channel`, `objective`, `industry`, `brand`, `date`, `source`.

**Where this data comes from (in priority order):**
1. **Meta Ads Manager export** — break down an ad set's ads by CTR/CVR. Each
   ad in the same ad set = one `test_id`, each creative = one row. This is the
   single richest source and most ecommerce advertisers already have it.
2. **TikTok Ads Manager** split tests — same structure.
3. **Email A/B tests** (Klaviyo, Mailchimp) — subject-line tests map directly:
   `test_id` = campaign, `creative_text` = subject line, `impressions` = sends,
   `clicks` = opens or clicks.
4. **Shopify / landing-page A/B tools** (e.g. Google Optimize successors).
5. **Your own past simulations that were later run for real** — close the loop.

## How to train on it

```bash
# 1. Map your export to the schema (write a small adapter like
#    validation_data/outcomes/adapt_upworthy.py, or hand-format to the template)
# 2. Build within-test pairs + train, honest test-id split, tradeoff curve:
python3 validation_data/outcomes/train_outcome_ranker.py \
    validation_data/outcomes/<your>_arms.csv \
    validation_data/outcomes/<your>_pairs.csv \
    models/creative_ranker_outcome_candidate.joblib
```

The artifact is drop-in compatible with `src/ai/creative_ranker.py` (same
keys: scaler/model/threshold/pca/embedding_model). To ship it, back up the
current `models/creative_ranker.joblib` and copy the candidate over it — but
only after the honest holdout curve clears your bar on **ecommerce** data.

## Combining sources (when ecommerce data arrives)

With enough ecommerce A/B rows, train ecommerce-only. With few, warm-start
from Upworthy (pretrain on Upworthy, fine-tune on ecommerce) — the trainer
takes any schema-conforming CSV, so concatenating `source`-tagged arms and
letting the split stay test-id-based is the simplest first pass. Always report
the honest **ecommerce-holdout** curve, never the blended one, as the sellable
number.

## Current status

- ✅ Schema + loader + within-test significance-filtered pairing
- ✅ Trainer with leakage-safe test-id split + honest tradeoff curve
- ✅ Proven on 5,860 real Upworthy pairs → 75–78% at 50–60% call rate
- ⏳ **Waiting on real ecommerce A/B exports** to fine-tune to ecommerce and
  ship a genuine ecommerce 75%. This is the one input the model can't
  synthesize — it must come from real campaigns.
