"""Static configuration for gui1: asset paths and shared constants."""

from __future__ import annotations

from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = Path(__file__).resolve().parents[3]  # repo root

ASSETS = _HERE / "assets"
LOGO = ASSETS / "taketwo.svg"
EMPTY_ART = ASSETS / "empty.svg"
SAMPLE_APP = _ROOT / "demo" / "scenarios" / "booking" / "app"

TAGLINE = "A screen recording in. A reproduction, a fix, and before/after proof out."

ACCEPTED = ["mp4", "mov", "webm", "mkv", "png", "jpg", "jpeg", "webp"]
VERDICT_LABELS = {"All": None, "Reproduced": "reproduced", "Not reproduced": "not_reproduced", "Unclear": "unclear"}
