# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
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

### Changed
- User-facing errors now show a friendly message + short error id; full
  tracebacks are logged server-side instead of being rendered to users.
- Report PDF text sanitized to Latin-1 so fpdf can't crash the History tab.

### Fixed
- Marketing Intelligence Dashboard call restored after it was dropped in merges.
- Copilot and background no longer rely on cross-origin `window.parent`
  injection (blocked by Streamlit Cloud's sandboxed iframes).
