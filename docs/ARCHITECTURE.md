# Architecture Overview

## System at a glance

The Digital Wind Tunnel is a **Streamlit multi-page app** backed by **Supabase**
(auth + Postgres) with an agent-based simulation engine and an ML CTR predictor.

```
Browser ──▶ Streamlit (app.py + pages/)
                │
                ├─ src/ui/        presentation (theme, copilot, history, dashboard)
                ├─ src/core/      cross-cutting: auth, supabase client, logging,
                │                 validation, health
                ├─ src/services/  persistence (reports, campaigns) over Supabase
                ├─ src/simulation/ agent engine (OCEAN + Prospect Theory)
                ├─ src/ai/        CTR ensemble, feature extraction, copilot
                └─ src/agents/    population generation
                        │
                        ▼
                   Supabase (Auth, Postgres + RLS)
```

## Request / data flow

1. **Auth** — `src/core/auth_utils` + `src/ui/auth_ui` gate every page except the
   public landing. Sessions live in `st.session_state["user"]`; Supabase issues
   and refreshes the tokens.
2. **Simulation** — `app.py` collects ad inputs, `src/agents` generates a cached
   agent population, `src/simulation/ab_test_runner` runs the A/B test, results
   render via `src/ui/dashboard_ui` and auto-save through
   `src/services/persistence_service` (RLS-scoped to the user).
3. **AI prediction** — `src/ai/predictor` prefers `src/ai/ensemble_predictor`
   (MiniLM embeddings + text stats → Ridge/HGB/MLP blend), falling back to the
   legacy model then the classic engine.
4. **Copilot** — `src/ai/copilot` calls the configured LLM, degrading to a
   heuristic fallback when no key/network is available.

## Cross-cutting concerns

| Concern | Module | Notes |
|---|---|---|
| Logging | `src/core/logging_config` | `get_logger`, `report_error` (returns opaque id), `safe_block` (component isolation) |
| Validation | `src/core/validation` | email/password policy, text bounding |
| Health | `src/core/health` | reachable at `?health=1` (Streamlit has no HTTP routing) |
| Persistence | `src/services/persistence_service` | thin layer over `SupabaseManager` with local-mode fallback |
| Secrets | env / `st.secrets` | never hardcoded; see `.env.example` |

## Resilience model

- Each major UI section is wrapped in `safe_block(...)`, so a failure is logged
  and shown as a friendly message without blanking the page.
- External calls (DB, LLM, file I/O, OCR) are individually guarded with
  graceful fallbacks.
- Heavy models (MiniLM, the ensemble) load lazily to respect Streamlit Cloud's
  memory budget.

## Known platform constraints

- **No HTTP endpoints**: Streamlit can't expose a real `/health`; we use a query
  parameter instead.
- **Sandboxed component iframes**: `components.html` runs cross-origin, so JS
  can't touch `window.parent.document`. Backgrounds/animations must be either
  self-contained iframes or pure CSS on the main document.
- **Sessions**: managed by Streamlit + Supabase; the app does not set its own
  HttpOnly cookies (not exposed by the framework).

## The ML benchmark is synthetic

The CTR ensemble is trained on a **synthetic development benchmark** because no
public dataset pairs English ad *creative text* with real CTR at scale. All
reported accuracy is a software benchmark, not a real-world claim. See
`data/dataset_card.md` and `docs/ACCURACY_UPGRADE_REPORT.md`.
