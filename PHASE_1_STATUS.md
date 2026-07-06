# Phase 1 Status: Stabilized

## Completion Summary
Phase 1 stabilization is complete. The simulation prototype is now reliable, deterministic, and internally consistent.

### Completed Tasks
- **API Unification**: Logic merged into `src/api/main.py`. Both root `/` and `/api/` prefixes are supported.
- **Deterministic Behavior**: Seed support implemented in `MaxSimulation`, `Agent` generation, and conversion decisions.
- **Dependency Optimization**: Split `requirements.txt` (lightweight) and `requirements-ml.txt` (neural scorer).
- **Neural Scorer Reliability**: Fixed model loading bugs and implemented robust fallbacks to heuristic scoring.
- **A/B Testing Alignment**: Winner selection and lift calculation now use a consistent objective.
- **Validation**: Strict Pydantic input validation for channels, agent counts, and ad scores.
- **CI/CD**: GitHub Actions workflow added for automated testing.

## How to Run

### Installation
- **Lightweight (Default)**: `pip install -r requirements.txt`
- **Full (Neural Scoring)**: `pip install -r requirements.txt -r requirements-ml.txt`

### Tests
- Run all stable tests: `pytest tests/`
- Verified suite: `pytest tests/test_api_v2.py`

### API
- Start server: `uvicorn api:app --reload`
- Access docs: `http://localhost:8000/docs`

### Streamlit Dashboard
- Start dashboard: `streamlit run app.py`

## Current API Routes
- `GET /health` | `GET /api/health`: System status
- `POST /simulate` | `POST /api/simulate`: Run single ad simulation (supports `seed`)
- `POST /calibrate` | `POST /api/calibrate`: Update calibrator with historical data
- `GET /agents`: List available agent profiles
- `POST /legacy_simulate`: Original prototype endpoint (backward compatibility)

## Determinism
The `seed` parameter in `/simulate` ensures reproducibility.
- Same seed + Same input = Identical results.
- Seed controls agent personality generation and probabilistic decisions.

## Known Risks
- **Heuristic Quality**: If ML dependencies are missing, the engine uses a keyword-based heuristic which is less nuanced than the neural model.
- **Legacy Components**: Some legacy tests require a live server on port 8000 and are skipped by default in local `pytest` runs.

**Note: Do not start Phase 2 without a separate, approved implementation plan.**
