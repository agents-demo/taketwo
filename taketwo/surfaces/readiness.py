"""Environment readiness checks surfaced by the GUIs.

Light: reads env vars directly (no heavy backend import) plus a couple of cheap
probes, so the Runs page can show what is configured *before* a run is started.
"""

from __future__ import annotations

import importlib.util
import os

from dotenv import load_dotenv

from taketwo.integrations.storage import runtime

load_dotenv()


def _model_ok() -> bool:
    return all(os.getenv(k) for k in ("API_KEY", "API_BASE", "MODEL_NAME"))


def checks() -> list[dict]:
    """The readiness checks, in display order."""
    model_ok = _model_ok()
    browser_ok = importlib.util.find_spec("playwright") is not None
    github_ok = bool(os.getenv("GITHUB_TOKEN"))
    clip = runtime.DATA_DIR / "sample_bug_live.mov"
    return [
        {
            "name": "model",
            "ok": model_ok,
            "detail": os.getenv("MODEL_NAME") or "set API_KEY / API_BASE / MODEL_NAME in .env",
        },
        {
            "name": "browser",
            "ok": browser_ok,
            "detail": "playwright" if browser_ok else "pip install -r requirements.txt && playwright install chromium",
        },
        {
            "name": "delivery",
            "ok": github_ok,
            "detail": "GITHUB_TOKEN set (draft PRs enabled)" if github_ok else "no GITHUB_TOKEN — issue/draft PR disabled",
        },
        {
            "name": "sample",
            "ok": clip.exists(),
            "detail": "sample clip ready" if clip.exists() else "run: python scripts/samples/make_sample_bug.py",
        },
    ]


def ready() -> bool:
    return all(c["ok"] for c in checks())
