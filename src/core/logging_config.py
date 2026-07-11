"""
Central logging configuration and safe error handling.

Two things every part of the app should use instead of `print` / leaking
tracebacks to users:

* ``get_logger(__name__)`` — a configured logger (level from ``LOG_LEVEL`` env).
* ``report_error(...)`` — logs the full traceback server-side and returns a
  short, opaque error id so the UI can show "something went wrong (id: ab12cd)"
  without exposing internals.
* ``safe_block(...)`` — a context manager that isolates a UI component: if it
  raises, the error is logged and a friendly message is shown, but the rest of
  the page keeps rendering.
"""
from __future__ import annotations

import logging
import os
import traceback
import uuid
from contextlib import contextmanager

_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for `name` (module __name__)."""
    _configure_root()
    return logging.getLogger(name)


def report_error(logger: logging.Logger, exc: BaseException, context: str = "") -> str:
    """Log an exception with a full traceback and return a short error id.

    The id is safe to show to end users; the traceback is never exposed to them.
    """
    error_id = uuid.uuid4().hex[:8]
    logger.error(
        "error_id=%s context=%s exc=%s\n%s",
        error_id, context or "-", exc,
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    )
    return error_id


@contextmanager
def safe_block(component: str, logger: logging.Logger | None = None):
    """Isolate a UI component. On failure, log it and show a friendly message.

    Usage:
        with safe_block("history tab"):
            render_history_tab()
    """
    log = logger or get_logger("app")
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - deliberate top-level isolation
        error_id = report_error(log, exc, context=component)
        try:
            import streamlit as st
            st.error(
                f"⚠️ The **{component}** section hit an unexpected error and was "
                f"skipped. The rest of the page is unaffected. (error id: `{error_id}`)"
            )
        except Exception:  # pragma: no cover - streamlit not available
            pass
