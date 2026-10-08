"""Stage: reproduce the inferred bug in a real browser.

Owns the browser: opens the session (stashing it on the run session so the prove stage
re-runs through the same object), grounds the inferred steps on the live page's
accessibility outline with the stage agent when a model is configured, replays them,
and records the **before** clip. When no browser is available it degrades to an
``unclear`` verdict with one clarifying question rather than guessing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taketwo.domain import repro as repro_mod
from taketwo.pipeline import agent_reply
from taketwo.pipeline.progress import Progress, tick
from taketwo.pipeline.stages.reproduce import browser, prompts, replay_steps
from taketwo.storage import runtime


def _sidecar(video_path: str) -> dict[str, Any] | None:
    path = Path(f"{video_path}.repro.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _ground_agent(run_session: Any) -> Any:
    """Build the grounding agent (best-effort; ``None`` without a configured model)."""
    try:
        from taketwo.pipeline.stages.reproduce.build_agent import build_agent

        recorder = getattr(run_session, "recorder", None)
        return build_agent(recorder=recorder).agent
    except Exception:
        return None


async def _ground(steps: list[dict], outline: str, run_session: Any) -> list[dict]:
    """Map inferred steps onto live selectors via the model (falls back to raw steps)."""
    if not steps or not outline:
        return steps
    agent = _ground_agent(run_session)
    if agent is None:
        return steps
    try:
        text = await agent_reply.ask(agent, prompts.build_user({"steps": steps}, outline))
        grounded = agent_reply.extract_json(text).get("steps")
        return grounded if grounded else steps
    except Exception:
        return steps


async def reproduce(
    video_path: str,
    timeline: dict[str, Any],
    app_url: str,
    job: str,
    progress: Progress | None = None,
    run_session: Any = None,
) -> dict[str, Any]:
    """Return a normalized reproduction for ``timeline`` against ``app_url``."""
    sidecar = _sidecar(video_path)
    if sidecar is not None:
        return repro_mod.normalize(sidecar)

    tick(progress, "reproducing in browser", 45)

    session = getattr(run_session, "browser", None)
    if session is None:
        session = browser.open_session(app_url)
        if run_session is not None:
            run_session.browser = session

    steps = timeline.get("steps", [])
    if session.live:
        steps = await _ground(steps, session.outline(), run_session)

    before_console = len(session.console)
    records = replay_steps.replay(session, steps)
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
