"""Stage: turn a recording into a normalized timeline.

Order of preference: a sidecar ``<video>.timeline.json`` (the deterministic demo
path), then the vision agent (when a model is configured), then a conservative
fallback that never claims more than the motion it measured.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taketwo import config
from taketwo.analysis import agent_reply
from taketwo.analysis.media import clips, cursor
from taketwo.analysis.media import frames as frames_mod
from taketwo.analysis.progress import Progress, tick
from taketwo.analysis.stages.understand import prompts
from taketwo.domain import timeline as timeline_mod
from taketwo.storage import runtime


def _sidecar(video_path: str) -> dict[str, Any] | None:
    path = Path(f"{video_path}.timeline.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _steps_from_motion(clicks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if clicks:
        return [
            {
                "action": "click",
                "timestamp": click["timestamp"],
                "confidence": 0.4,
                "evidence": f"motion {click['score']}",
            }
            for click in clicks
        ]
    return [{"action": "wait", "timestamp": 0.0, "confidence": 0.1, "evidence": "no motion detected"}]


async def understand(video_path: str, progress: Progress | None = None, agent: Any = None) -> dict[str, Any]:
    """Return a normalized timeline for ``video_path``."""
    tick(progress, "reading recording", 8)
    _meta, frames, timestamps = frames_mod.sample_frames(video_path, config.frame_fps(), config.max_frames())
    clicks = cursor.detect_clicks(frames, timestamps, config.cursor_threshold())

    sheet = clips.contact_sheet(frames, timestamps)
    sheet_path = None
    if sheet is not None:
        sheet_path = clips.save_image(sheet, runtime.ARTIFACTS_DIR / f"{Path(video_path).stem}_contact.png")

    sidecar = _sidecar(video_path)
    if sidecar:
        return timeline_mod.normalize(sidecar)

    if agent is not None:
        tick(progress, "inferring steps", 30)
        try:
            text = await agent_reply.ask(agent, prompts.build_user(sheet_path, clicks))
            data = agent_reply.extract_json(text)
            if data.get("steps"):
                return timeline_mod.normalize(data)
        except Exception:
            pass

    return timeline_mod.normalize(
        {"steps": _steps_from_motion(clicks), "failure": {"summary": "", "timestamp": 0.0, "signal": ""}}
    )
