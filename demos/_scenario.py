"""Locate and load demo scenarios (``demos/scenarios/<name>/``)."""

from __future__ import annotations

import json
from pathlib import Path

SCENARIOS = Path(__file__).resolve().parent / "scenarios"


def names() -> list[str]:
    return sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir())


def path(name: str) -> Path:
    return SCENARIOS / name


def app_dir(name: str) -> Path:
    return path(name) / "app"


def clip(name: str) -> Path:
    return path(name) / "clip.mp4"


def load(name: str) -> dict:
    return json.loads((path(name) / "scenario.json").read_text(encoding="utf-8"))
