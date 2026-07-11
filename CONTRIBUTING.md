# Contributing

Thanks for helping improve the Digital Wind Tunnel. This guide covers the
workflow, coding standards, and how to run checks locally.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in Supabase + (optional) AI keys
streamlit run app.py
```

Never commit real secrets. `.env` and `.streamlit/secrets.toml` are gitignored;
`.env.example` documents every variable with placeholders.

## Coding standards

- **Style:** [Black](https://black.readthedocs.io/) (line length 100) +
  [Ruff](https://docs.astral.sh/ruff/) for linting. Config lives in
  `pyproject.toml`.
  ```bash
  black . && ruff check .
  ```
- **Type hints** on all new functions and methods.
- **Docstrings** on every module, class, and public function.
- **Logging, not print:** use `from src.core.logging_config import get_logger`.
  Never show a raw traceback to a user — use `report_error(...)` and display the
  returned short error id.
- **Input validation:** validate user input with `src/core/validation.py`
  helpers. Never pass user text into `st.markdown(..., unsafe_allow_html=True)`.
- **Component isolation:** wrap independent UI sections in `safe_block(...)` so
  one failure can't blank the page.

## Tests

```bash
pytest
```

Add unit tests under `tests/` for any new logic (feature extraction, prediction,
validation, simulation). Keep tests fast and deterministic (`random_state=42`).

## Pull requests

1. Branch from `main`.
2. Keep PRs focused; describe the change and how you tested it.
3. Ensure `black`, `ruff`, and `pytest` pass.
4. Update `CHANGELOG.md` and any affected docs.

## Security

Report suspected vulnerabilities privately to the maintainers rather than in a
public issue. Do not include real credentials in issues, PRs, or test fixtures.
