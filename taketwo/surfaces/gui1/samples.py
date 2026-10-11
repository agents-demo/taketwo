"""Sample clip + sample-app helpers for the one-tap demo (the booking scenario)."""

from __future__ import annotations

import sys

import streamlit as st

from taketwo.surfaces.gui1 import config


def sample_path() -> str:
    """The demo recording (``demos/scenarios/booking/clip.mp4``), or ``""`` if missing."""
    return str(config.SAMPLE_CLIP) if config.SAMPLE_CLIP.exists() else ""


def live_sample_path() -> str:
    return sample_path()


def sample_app_url(port: int = 8130) -> str:
    """Serve ``demos/scenarios/booking/app`` locally once and return its URL."""
    cached = st.session_state.get("_sample_app")
    if cached is not None:
        return getattr(cached, "url", "")
    if not config.SAMPLE_APP.exists():
        return ""
    from taketwo.integrations import appserver

    command = f'"{sys.executable}" -m http.server {port} --directory "{config.SAMPLE_APP}"'
    app = appserver.start(command, config._ROOT, f"http://localhost:{port}")
    if app is not None:
        st.session_state["_sample_app"] = app
        return app.url
    return ""
