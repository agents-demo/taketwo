"""Shared run state for one reproduction.

Wires the run recorder, the browser session and the media dir in one place, so the
``reproduce`` and ``prove`` stages share a single browser. Building the understand
vision agent is best-effort: without a configured model the run degrades to the
deterministic media path instead of failing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from taketwo.analysis.browser import open_session
from taketwo.analysis.stages.understand.build_agent import build_agent as build_vision_agent
from taketwo.storage import runtime


@dataclass
class RunSession:
    """The run recorder, the browser session and the media dir for a single run."""

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


def start_session(job: str, app_url: str = "") -> RunSession:
    """Wire a run: build the understand agent (best-effort) and open the browser."""
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

    browser = open_session(app_url) if app_url else None
    return RunSession(job=job, recorder=recorder, browser=browser, media_dir=media_dir, vision_agent=vision_agent)
