"""Sample clip + sample-app helpers for the one-tap live demo."""

from __future__ import annotations

import sys

import streamlit as st

from taketwo.storage import runtime
from taketwo.surfaces.gui1 import config


def sample_path() -> str:
    path = runtime.DATA_DIR / "sample_bug.mov"
    return str(path) if path.exists() else ""


def live_sample_path() -> str:
    """The live-sample clip (timeline only, no repro sidecar → reproduces in a browser)."""
    path = runtime.DATA_DIR / "sample_bug_live.mov"
    return str(path) if path.exists() else sample_path()


def sample_app_url(port: int = 8130) -> str:
    """Serve ``examples/sample_app`` locally once and return its URL (for the live demo)."""
    cached = st.session_state.get("_sample_app")
    if cached is not None:
        return getattr(cached, "url", "")
    if not config.SAMPLE_APP.exists():
        return ""
    from taketwo.pipeline import appserver

    command = f'"{sys.executable}" -m http.server {port} --directory "{config.SAMPLE_APP}"'
    app = appserver.start(command, config._ROOT, f"http://localhost:{port}")
    if app is not None:
        st.session_state["_sample_app"] = app
        return app.url
    return ""
