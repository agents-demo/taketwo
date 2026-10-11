"""Demo-scenario helpers for the one-tap run (reads ``demos/scenarios/``)."""

from __future__ import annotations

import json
import sys

import streamlit as st

from taketwo.surfaces.gui1 import config


def scenario_names() -> list[str]:
    root = config.SCENARIOS_DIR
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "app" / "index.html").is_file())


def scenario_title(name: str) -> str:
    try:
        data = json.loads((config.SCENARIOS_DIR / name / "scenario.json").read_text(encoding="utf-8"))
        return data.get("title") or name
    except Exception:
        return name


def scenario_clip(name: str) -> str:
    path = config.SCENARIOS_DIR / name / "clip.mp4"
    return str(path) if path.exists() else ""


def serve_scenario(name: str, port: int = 8130) -> str:
    """Serve a scenario's app locally and return its URL (one demo app at a time, cached)."""
    current = st.session_state.get("_demo_app_name")
    app = st.session_state.get("_demo_app")
    if app is not None and current == name:
        return getattr(app, "url", "")

    from taketwo.integrations import appserver

    if app is not None:
        appserver.stop(app)
        st.session_state.pop("_demo_app", None)

    app_dir = config.SCENARIOS_DIR / name / "app"
    if not app_dir.is_dir():
        return ""
    command = f'"{sys.executable}" -m http.server {port} --directory "{app_dir}"'
    app = appserver.start(command, config._ROOT, f"http://localhost:{port}")
    if app is not None:
        st.session_state["_demo_app"] = app
        st.session_state["_demo_app_name"] = name
        return app.url
    return ""
