"""Stage: reproduce the inferred bug in a real browser.

Opens a session (shared with the prove stage), replays the steps, captures the
console/network around the failure, and records the **before** clip. When no
browser is available it degrades to an ``unclear`` verdict with one clarifying
question rather than guessing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taketwo.browser import open_session
from taketwo.domain import repro as repro_mod
from taketwo.pipeline.progress import Progress, tick
from taketwo.pipeline.stages.reproduce import replay_steps
from taketwo.storage import runtime


def _sidecar(video_path: str) -> dict[str, Any] | None:
    path = Path(f"{video_path}.repro.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def reproduce(
    video_path: str,
    timeline: dict[str, Any],
    app_url: str,
    job: str,
    progress: Progress | None = None,
    session: Any = None,
) -> dict[str, Any]:
    """Return a normalized reproduction for ``timeline`` against ``app_url``."""
    sidecar = _sidecar(video_path)
    if sidecar is not None:
        return repro_mod.normalize(sidecar)

    tick(progress, "reproducing in browser", 45)

    session = session or open_session(app_url)
    before_console = len(session.console)
    records = replay_steps.replay(session, timeline.get("steps", []))
    new_console = session.console[before_console:]
    signal = replay_steps.failure_signal(new_console)

    before_clip = session.snapshot(runtime.ARTIFACTS_DIR / job / "before.png") if session.live else None

    if signal:
        verdict = "reproduced"
    elif session.live:
        verdict = "not_reproduced"
    else:
        verdict = "unclear"

    return repro_mod.normalize(
        {
            "steps": records,
            "evidence": {"console": new_console, "network": session.network, "dom": "", "summary": signal},
            "verdict": verdict,
            "before_clip": before_clip or "",
            "question": "" if verdict != "unclear" else "Which element did you click, and what did you expect?",
        }
    )
