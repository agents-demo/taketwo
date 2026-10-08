"""The inferred timeline: the ordered steps the reporter took and where it failed.

Pure. A timeline is ``{"steps": [...], "failure": {...}}``; each step is
``{"index", "action", "target", "value", "timestamp", "confidence", "evidence"}``.
"""

from __future__ import annotations

from typing import Any

ACTIONS = {"click", "type", "select", "hover", "navigate", "key", "wait", "scroll", "unknown"}


def normalize_step(step: dict[str, Any], index: int) -> dict[str, Any]:
    action = str(step.get("action", "unknown")).lower()
    return {
        "index": int(step.get("index", index)),
        "action": action if action in ACTIONS else "unknown",
        "target": str(step.get("target", "") or ""),
        "value": str(step.get("value", "") or ""),
        "timestamp": float(step.get("timestamp", 0.0) or 0.0),
        "confidence": float(step.get("confidence", 0.0) or 0.0),
        "evidence": str(step.get("evidence", "") or ""),
    }


def normalize(data: dict[str, Any] | None) -> dict[str, Any]:
    """Coerce an arbitrary object into the canonical timeline shape."""
    data = data or {}
    steps = [normalize_step(s, i) for i, s in enumerate(data.get("steps", []) or [])]
    failure = data.get("failure") or {}
    return {
        "steps": steps,
        "failure": {
            "summary": str(failure.get("summary", "") or ""),
            "timestamp": float(failure.get("timestamp", 0.0) or 0.0),
            "signal": str(failure.get("signal", "") or ""),
        },
    }


def describe(timeline: dict[str, Any]) -> str:
    """Human-readable one-line-per-step rendering."""
    lines: list[str] = []
    for step in timeline.get("steps", []):
        target = step.get("target") or "?"
        value = f" = {step['value']!r}" if step.get("value") else ""
        lines.append(f"{step['index'] + 1}. {step['action']} {target}{value} (t={step['timestamp']:.2f}s)")
    return "\n".join(lines) if lines else "(no steps inferred)"


def validate(timeline: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if not timeline.get("steps"):
        problems.append("timeline has no steps")
    for step in timeline.get("steps", []):
        if step.get("action") == "unknown":
            problems.append(f"step {step.get('index')} has an unknown action")
    return problems
