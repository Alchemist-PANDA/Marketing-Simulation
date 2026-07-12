# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

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
