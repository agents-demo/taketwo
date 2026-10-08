"""Shared run state for one reproduction.

Holds the run recorder, the media dir and the slots the stages fill in. The
understand vision agent is built here (best-effort); the browser session is opened
by the ``reproduce`` stage, which owns the browser, and stashed on ``browser`` so the
prove after-clip can reuse it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from taketwo.pipeline.stages.understand.build_agent import build_agent as build_vision_agent
from taketwo.storage import runtime


@dataclass
class RunSession:
    """The run recorder, media dir and stage-filled slots for a single run."""

    job: str
    recorder: Any = None
    browser: Any = None
    media_dir: Path | None = None
    vision_agent: Any = None

    def usage_summary(self) -> dict[str, Any]:
        if self.recorder is None:
            return {"calls": 0, "total_tokens": 0}
        text = self.recorder.text.summary() if self.recorder else {}
        vision = self.recorder.vision.summary() if self.recorder else {}
        return {
            "vision": vision,
            "text": text,
            "calls": int(vision.get("calls", 0)) + int(text.get("calls", 0)),
            "total_tokens": int(vision.get("total_tokens", 0)) + int(text.get("total_tokens", 0)),
            "models": self.recorder.models() if self.recorder else {},
        }

    def save_details(self) -> str | None:
        """Persist model/tool calls to ``<job>_observability.json`` (best-effort)."""
        if self.recorder is None:
            return None
        try:
            path = runtime.ARTIFACTS_DIR / f"{self.job}_observability.json"
            path.write_text(
                json.dumps(
                    {"calls": self.recorder.calls.calls, "tools": self.recorder.tools.records()},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return str(path)
        except Exception:
            return None


def start_session(job: str) -> RunSession:
    """Wire a run: build the understand agent (best-effort). The browser is opened later."""
    media_dir = runtime.ARTIFACTS_DIR / job
    media_dir.mkdir(parents=True, exist_ok=True)

    recorder = None
    vision_agent = None
    try:
        built = build_vision_agent(media_dir=str(media_dir))
        recorder = built.recorder
        vision_agent = built.agent
    except Exception:
        recorder = None

    return RunSession(job=job, recorder=recorder, media_dir=media_dir, vision_agent=vision_agent)
