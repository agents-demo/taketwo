"""Paths and constants for the gui2 server."""

from __future__ import annotations

from pathlib import Path

from taketwo.integrations.storage import runtime

_HERE = Path(__file__).resolve().parent

CLIENT_BUILD = _HERE.parent / "client" / "build"  # the SvelteKit SPA (built static assets)
SAMPLE_APP = runtime.PROJECT_ROOT / "demo" / "booking"
UPLOADS = runtime.DATA_DIR / "uploads"

ACCEPTED = {".mp4", ".mov", ".webm", ".mkv", ".png", ".jpg", ".jpeg", ".webp"}
