"""Locate the demo scenario for a recording (a clip sitting next to ``scenario.json``).

Used to give demos a real fix + proof without a git repository: the scenario file
carries the fix (``patch`` / ``proof.find`` → ``proof.replace``) for its little app.
"""

from __future__ import annotations

import json
from pathlib import Path


def for_video(video_path: str) -> dict | None:
    """The demo scenario whose folder holds ``video_path``, or ``None``."""
    if not video_path:
        return None
    path = Path(video_path).parent / "scenario.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
