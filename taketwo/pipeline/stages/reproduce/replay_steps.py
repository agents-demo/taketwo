"""Replay a timeline against a browser session and collect the failure signal."""

from __future__ import annotations

from typing import Any

from taketwo import config
from taketwo.pipeline.stages.reproduce.browser.session import BrowserSession


def replay(session: BrowserSession, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Perform each step in order (capped) and return the step records."""
    records: list[dict[str, Any]] = []
    for step in steps[: config.max_steps()]:
        result = session.act(step.get("action", "wait"), step.get("target", ""), step.get("value", ""))
        records.append(
            {
                "index": step.get("index", len(records)),
                "action": step.get("action", "unknown"),
                "target": step.get("target", ""),
                "value": step.get("value", ""),
                "timestamp": step.get("timestamp", 0.0),
                "confidence": step.get("confidence", 0.0),
                "ok": result.ok,
                "detail": result.detail,
            }
        )
    return records


def failure_signal(console: list[str]) -> str:
    """The first console/page error, if any (the evidence that it reproduced)."""
    for line in console:
        low = line.lower()
        if "pageerror" in low or "error" in low or "uncaught" in low:
            return line.strip()
    return ""
