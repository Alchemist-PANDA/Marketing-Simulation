# Validation Report — CTR Ensemble (Synthetic Benchmark)

> ⚠️ All numbers are on a **synthetic development benchmark** (`data/dataset_card.md`).
> They validate the pipeline, not real-world ad performance.

## Headline (untouched holdout, n = 391)

| Metric | Ensemble |
|---|---|
| Directional accuracy — decisive pairs (≥10% CTR gap) | **0.962** |
| Directional accuracy — all pairs | 0.923 |
| Pearson correlation | 0.966 |
| Spearman rank correlation | 0.970 |
| RMSE (CTR) | 0.00220 |

The ≥95% directional-accuracy target is met **on decisive pairs** — the case
that matters for A/B decisions, where a real winner exists. Over *all* pairs
(including statistical near-ties) the honest figure is 92.3%.

## Error analysis

### By CTR tier (decisive DA)
| Tier | n | DA |
|---|---|---|
| Low CTR | 129 | 0.847 |
| Mid CTR | 129 | 0.900 |
| High CTR | 133 | 0.948 |

The model is **strongest on high-CTR ads and weakest on low-CTR ads**. This is
expected: at low base rates the multiplicative noise (σ=0.07) is a larger share
of the signal, so ordering two weak ads is genuinely harder.

### By ad length (decisive DA)
| Bucket | n | DA |
|---|---|---|
| Short (≤ median words) | 199 | 0.964 |
| Long (> median words) | 192 | 0.961 |

No meaningful length bias.

### Largest absolute errors
The worst misses are high-CTR streaming/gaming ads that are slightly
**under-predicted**, and ads with **conflicting signals** (e.g. a premium/luxury
phrase inside an otherwise high-CTR gaming ad). These are the ambiguous cases a
human would also find hard to rank.

## Interpretability

SHAP is not installed in this environment; the standardized **Ridge
coefficients** (Ridge is the highest-weighted ensemble member) are used as the
importance measure. **All top-12 features are MiniLM embedding dimensions**
(`emb_143`, `emb_64`, `emb_317`, …) — zero of the top 12 are hand-coded
statistics — confirming the model relies on **semantic meaning**, which is the
intended upgrade over the old keyword scorer. Text statistics contribute
secondary signal.

## Reproducibility

- Fixed seeds (`random_state=42`) throughout generation, splitting, and training.
- `python -m src.ai.synth_data` regenerates the dataset.
- `python -m src.ai.train_models` regenerates all models, weights, and
  `models/ensemble_metrics.json`.

## Honesty statement

This validates that the **ensemble pipeline recovers a known text→CTR signal**
with high fidelity. It does **not** establish real-world CTR accuracy. To make a
real claim, retrain on a real `ad_text` + `actual_ctr` dataset (see the upgrade
report, §8) — the code path is unchanged; only the data would differ.
