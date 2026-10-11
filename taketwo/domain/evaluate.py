"""Pure scoring of a reproduction (evidence coverage, grounding).

Used by the UI, the benchmark and ``scripts/evaluate_repros.py`` to keep quality
visible instead of trusting the agent's word.
"""

from __future__ import annotations

from typing import Any


def score(reproduction: dict[str, Any]) -> dict[str, Any]:
    steps = reproduction.get("steps", [])
    evidence = reproduction.get("evidence", {})
    total = len(steps) or 1

    targeted = sum(1 for s in steps if s.get("target"))
    confident = sum(1 for s in steps if float(s.get("confidence", 0.0)) >= 0.5)
    has_signal = bool(evidence.get("summary")) or bool(evidence.get("console"))

    coverage = round(targeted / total, 3)
    confidence = round(confident / total, 3)
    reproduced = reproduction.get("verdict") == "reproduced"

    flags: list[str] = []
    if not has_signal and reproduced:
        flags.append("claims reproduced without an evidence signal")
    if coverage < 0.5 and steps:
        flags.append("most steps have no target")

    return {
        "verdict": reproduction.get("verdict", "unclear"),
        "target_coverage": coverage,
        "confidence_ratio": confidence,
        "has_signal": has_signal,
        "grounded": has_signal and coverage >= 0.5,
        "flags": flags,
        "score": round((coverage + confidence) / 2, 3),
    }
