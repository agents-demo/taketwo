"""The reproduction: what happened when we replayed the steps in a browser.

Pure. A reproduction is ``{"steps", "evidence", "verdict", "before_clip", "question"}``.
"""

from __future__ import annotations

from typing import Any

from taketwo.domain import timeline as timeline_mod

VERDICTS = {"reproduced", "not_reproduced", "unclear"}


def normalize(data: dict[str, Any] | None) -> dict[str, Any]:
    data = data or {}
    verdict = str(data.get("verdict", "unclear")).lower()
    evidence = data.get("evidence") or {}
    steps = [timeline_mod.normalize_step(s, i) for i, s in enumerate(data.get("steps", []) or [])]
    return {
        "steps": steps,
        "evidence": {
            "console": [str(x) for x in evidence.get("console", []) or []],
            "network": [str(x) for x in evidence.get("network", []) or []],
            "dom": str(evidence.get("dom", "") or ""),
            "summary": str(evidence.get("summary", "") or ""),
        },
        "verdict": verdict if verdict in VERDICTS else "unclear",
        "before_clip": str(data.get("before_clip", "") or ""),
        "question": str(data.get("question", "") or ""),
    }


def validate(reproduction: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if reproduction.get("verdict") not in VERDICTS:
        problems.append("verdict must be reproduced | not_reproduced | unclear")
    if reproduction.get("verdict") == "reproduced" and not reproduction.get("evidence", {}).get("summary"):
        problems.append("a reproduced bug needs an evidence summary")
    return problems
