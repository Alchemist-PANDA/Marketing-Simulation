# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added (2026-07-12) — outcome-based training pipeline (the real path to 75%)
- **Built and proved the pipeline that trains the ranker on labels that
  depend on the creative** (real A/B test results), the answer to v7's finding
  that TikTok CTR tiers cap out at ~55%. New `src/ai/outcomes/ab_outcome_schema.py`
  ingests one-row-per-variant A/B data, forms **within-test** pairs (same
  audience isolates the creative), filters by a 2-proportion significance test,
  and splits by test id (no variant leaks across train/holdout).
- **Proof on the Upworthy Research Archive** (4,873 real headline A/B tests,
  5,860 pairs): **69.1% ungated (n=1,005), 75.3% at 60% call rate, 78.1% at 50%
  call rate** — stable, monotonic confidence gating, vs ~55%/2-3% on TikTok
  tiers. Confirms text carries real learnable click-signal when the label
  isolates the creative; the bottleneck was always the label, not the model.
  (Honest caveat: Upworthy is news headlines, a pretraining/proof source, not
  the shipped ecommerce model — it scores ~55% on the noisy TikTok ecommerce
  labels.) Trainer: `validation_data/outcomes/train_outcome_ranker.py`; input
  template: `validation_data/outcomes/TEMPLATE_ab_outcomes.csv`; full roadmap:
  `docs/OUTCOME_TRAINING.md`.
- **Ready for real ecommerce A/B exports** (Meta/TikTok Ads Manager, email
  A/B, Shopify) through the same schema to fine-tune toward a genuine ecommerce
  75%. That real-campaign data is the one input the model can't synthesize.

### Changed (2026-07-12) — creative ranker v7: leakage + calibration fixes, honest ceiling
- **Corrected two methodology bugs that were inflating every prior version's
  accuracy, and re-established the honest ceiling.** A $40 scrape (8 Apify
  keys × 275 ecommerce keywords) added 11,950 new unique ecommerce ads (corpus
  ~5× to 15,008). Processing it surfaced: (1) **text leakage** — keyword search
  returns identical ad copy under many ad IDs with blank brands, which the
  brand-hash split scattered across train/holdout (18.7% of 4-wave holdout
  pairs, and 10.2% of v6's holdout, had a train-set text), letting the model
  memorize text→CTR; fixed with exact-text dedup + brand-else-text split (0%
  residual leakage); (2) a **train/deploy calibration mismatch** — the trainer
  tuned the abstention threshold on isotonic-calibrated confidence while the
  app gates on raw probability, and the isotonic step had gone degenerate on
  the larger data (fake 95%+ confidence); fixed by dropping isotonic and
  tuning/deploying on the same raw confidence.
- **Honest leakage-free result (v7, 1,112-pair holdout):** ~55% ungated (all
  model classes plateau ~52–53% on val — a data/label ceiling, not a model
  one). Confidence gating concentrates accuracy but is unstable across splits;
  val and holdout only agree at the top of the confidence range (threshold
  ~0.80), where pooled val+holdout is **81.8% (n=22, 95% CI 61.5–92.7%)** at a
  ~2–3% call rate. **The prior "80.6%" (v6) and "82.8%" (v4) figures were
  leakage- and small-sample-inflated and are retired.** A certified "75% on all
  ecommerce ads" is not achievable from TikTok CTR-tier data with text/thumbnail
  features — shown, not assumed, across 4 waves / ~13k ads. v7 ships at the
  conservative threshold 0.80 (abstains unless genuinely confident); the results
  UI states this honestly. Full account: `docs/VALIDATION.md` § "The v7 honest
  reckoning." Prior model kept at `models/creative_ranker_v6_backup.joblib`.
- **Video upload now actually feeds the model** (was silently discarded): a
  representative keyframe is run through the same trained image-feature path as
  thumbnails. See below.

### Added (2026-07-12) — creative ranker v6, ecommerce-focused rescrape
- **Shipped v6 of the creative ranker** (`models/creative_ranker.joblib`),
  trained on a third scrape wave targeted at fixing the ecommerce gap found
  earlier the same day (below). 24 varied TikTok Creative Center queries
  ($4.50 of a $5 budget) returned 3,071 raw items, 284 genuinely new after
  dedup, 175 ecommerce. Caught and fixed a data-quality bug before training:
  two scraped "brand names" were actually platform-wide promo campaigns
  (`Shopee Brands Festival`, 84 ads; `Celebrate 12.12 with Shopee`, 70 ads)
  that would have taught the model unrelated sellers' ads are same-brand
  variants — blanked before pairing, which removed ~5,928 spurious pairs.
  Retrained on the merged 3-wave corpus (3,058 ads, 3,710 pairs). **Real
  app-path result on the ecommerce holdout: 80.6% accuracy on called pairs
  (n=62, 95% CI 69.1–88.6%), same-brand accuracy 70.6% (n=17)** — up from
  0/5 same-brand correct two iterations earlier. Clears the 75%
  point-estimate target; CI lower bound (69.1%) means this should be
  communicated as "~80% in validation" rather than a guaranteed floor.
  Previous model kept at `models/creative_ranker_v5_backup.joblib`. Full
  account: `docs/VALIDATION.md` § "The v6 rescrape."

### Investigated (2026-07-12) — ecommerce vertical readiness (first attempt, superseded above)
- **Attempted to specialize the creative ranker for ecommerce and hit a
  defensible 75% accuracy floor for a business sale, using only
  already-scraped data (no `APIFY_TOKEN` available yet). Result: not there
  yet.** Filtered the existing two-wave corpus to 1,497 ecommerce ads /
  1,846 pairs. Training an ecommerce-only model from scratch made things
  *worse* (62.4% vs v5's 69.6%, same-brand fell to chance) — 1,498 pairs
  isn't enough data for this feature space. Re-tuning only the confidence
  threshold on ecommerce validation data and testing through the real
  `ABTestRunner` app path gave **70.5% accuracy on called pairs (n=44, 95%
  CI 55.8–81.8%)** — below target, and **same-brand pairs (comparing two of
  your own ad variants) scored 0/5 when called**. This result is what
  motivated getting a real scrape token and running the v6 rescrape above.

### Fixed (2026-07-12)
- **Creative ranker v4 → v5: fixed single-wave overfitting.** v4 (below)
  was trained and holdout-tested on ads from one scrape wave only. Tested
  against 285 genuinely new ads scraped a day later, it collapsed to 49.7%
  ungated accuracy (n=547, 95% CI 45.6–53.9%) — statistically pure chance,
  despite the fresh pairs matching the original holdout's CTR-gap
  distribution almost exactly. Root cause: brand-hash splitting within a
  single scrape wave doesn't test generalization across time, only across
  brands. **Fix:** merged both scrape waves (2,774 ads total) and re-split
  by brand-hash across the combined pool, so holdout now contains ads from
  both waves. Retrained (`models/creative_ranker.joblib`, old version kept
  at `models/creative_ranker_v4_backup.joblib`). New end-to-end result
  through the real app path: **69.8% on confident calls (95% CI 54.9–81.4%,
  n=43), 80.8% on decisive+called (95% CI 62.1–91.5%, n=26)**. This is
  centered at the 70% target but not a guaranteed floor — a fully
  independent third scrape wave for a true blind test wasn't obtainable
  this round (the scraper's top-ads leaderboard proved heavily saturated
  across query variations). Full honest account: `docs/VALIDATION.md`.
- **Pretraining data lake** (session-local, not committed): 330k+ real rows
  from Criteo 1TB Click Logs, Criteo Kaggle CTR, Avazu, iPinYou RTB, and
  Taobao ad-behavior, stored as independent pretraining satellites with
  zero fabricated joins to the TikTok creative hub. Not yet integrated into
  the ranker — see `docs/VALIDATION.md` for what that would take.

### Added
- **Validated creative ranker** (`src/ai/creative_ranker.py` +
  `models/creative_ranker.joblib`): pairwise model trained on 2,489 real
  TikTok ads / 3,211 outcome pairs (Creative Center CTR tiers via Apify),
  plus visual features trained on 1,374 real ad thumbnails. End-to-end
  holdout accuracy through the app path: **82.8% on confident calls, 87.5%
  on decisive+called** (call rate ~11–16%; the model honestly abstains on
  too-close races) — **superseded by v5 above; this figure was overfit to
  a single scrape wave and should not be quoted.** Replaces the keyword
  scorer as the winner decision — the old scorer measured 50.1% (pure
  chance) on real data. Full write-up incl. limitations: `docs/VALIDATION.md`.
- **Confidence verdict UI**: results now show either "🎯 Validated model
  pick (confidence N%)" or "⚖️ Too close to call — run both", instead of
  always declaring a winner.
- **Visual creative analysis** (`src/ai/visual_features.py`): PIL image
  features (brightness/contrast/colorfulness/edge density/aspect) feeding
  the ranker; OpenCV video frame sampling (hook strength, cut rate, motion
  energy) with graceful fallback when opencv is unavailable.
- **Validation pipeline** (`validation_data/`): dataset builder, thumbnail
  featurizer, leakage-safe trainer, and end-to-end backtest.
- **CTR ensemble** (Ridge + HistGradientBoosting + MLP) over MiniLM embeddings +
  text-statistic/sentiment features, with a validation-weighted blend and a
  documented synthetic benchmark (96.2% decisive-pair directional accuracy —
  clearly labeled as synthetic, not a real-world claim). See
  `docs/ACCURACY_UPGRADE_REPORT.md`.
- **3D galactic UI**: pure-CSS deep-space background (nebulae + parallax star
  layers) that renders reliably on Streamlit Cloud, applied across all pages.
- **Report History**: auto-save to Supabase, search/sort, CSV/JSON/PDF export,
  delete, with per-report render isolation.
- **AI Marketing Copilot**: self-contained galaxy chat header + native chat,
  file-upload context, graceful offline fallback.
- **Hardening**: central logging (`src/core/logging_config.py`), health check
  (`src/core/health.py`, exposed at `?health=1`), input validation
  (`src/core/validation.py`), stronger password policy.
- **Governance**: `LICENSE` (MIT), `CONTRIBUTING.md`, `pyproject.toml`
  (Black/Ruff/pytest), `docs/ARCHITECTURE.md`, and tests under `tests/`.

- **Video upload**: preview-and-run video input on the main A/B simulation and a
  video preview on the AI Predictions tab (MP4/MOV/AVI/WEBM/M4V). Copy still
  drives the model; automated frame/audio analysis is flagged as future work.
- **A/B/C testing**: the simulation now supports an optional third creative (Ad C)
  via a checkbox in Text mode. `ABTestRunner.run_test` splits the population into
  N disjoint cohorts (2 or 3); winner is the best of all variants and lift is
  measured vs. the runner-up. Results, engagement chart, and forensic feedback are
  variant-count-aware; the deep A-vs-B dashboard is unchanged. Two-variant output
  is fully backward-compatible.
- **Expert copilot foundation** (per `marketing_expert_copilot_plan.md`):
  - **In-app Gemini key entry** — a paste box appears in the copilot when no key
    is detected (runtime key source + reload path). Fixes "I added my key but it's
    still offline": there was previously no in-app place to enter a Gemini key the
    copilot actually reads.
  - **Persistent brand profile** (`src/ai/brand_profile.py`, Supabase table
    `brand_profiles`): business model (B2C/B2B/hybrid), stage, live budget, brand
    voice, ICP, competitors, channels, seasonality — injected into every copilot
    answer, with timestamped change-logging for corrections (plan §3.1/§3.6).
  - **Expert system prompt**: explicit brand-vs-performance tension flagging,
    business-model awareness, graceful correction handling, and honest guardrails
    (plan §1.7/§5/§6) — targets the §8 worked-example behavior.

### Fixed
- **Save-campaign RLS failure** (`new row violates row-level security policy for
  table "campaigns"`): the Supabase client was only ever using the anon key, so
  Postgres saw `auth.uid()` as NULL and rejected every insert. The logged-in
  user's JWT (from `st.session_state["access_token"]`) is now attached to every
  insert/select/update/delete via `SupabaseManager._apply_user_auth`, so RLS
  policies resolve the real user. Added an explicit, idempotent
  `supabase/migrations/20260711_campaigns_rls.sql`.
- **Copilot "offline" message accuracy**: the copilot was already fully on Gemini
  (endpoint, `?key=` auth, `contents/parts` payload, `candidates[…].text`
  parsing, multi-key rotation). The fallback banner now distinguishes *no key
  configured* ("add your Gemini API keys") from a *transient API/network error*
  ("temporarily unavailable — try again"), instead of always blaming missing keys.

### Changed
- User-facing errors now show a friendly message + short error id; full
  tracebacks are logged server-side instead of being rendered to users.
- Report PDF text sanitized to Latin-1 so fpdf can't crash the History tab.

### Fixed
- Marketing Intelligence Dashboard call restored after it was dropped in merges.
- Copilot and background no longer rely on cross-origin `window.parent`
  injection (blocked by Streamlit Cloud's sandboxed iframes).
