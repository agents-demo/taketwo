"""Heuristic cursor/click detection from frame differences.

Deliberately simple and dependency-optional: numpy is imported lazily, and an empty
result is a valid answer for a still or unreadable clip.
"""

from __future__ import annotations

from typing import Any


def _gray(frame: Any) -> Any:
    import numpy as np

    arr = np.asarray(frame, dtype="float32")
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    return arr


def motion_scores(frames: list) -> list[float]:
    """Mean absolute frame-to-frame difference (0 when fewer than 2 frames)."""
    if len(frames) < 2:
        return []
    try:
        import numpy as np

        scores: list[float] = []
        prev = _gray(frames[0])
        for frame in frames[1:]:
            cur = _gray(frame)
            if cur.shape != prev.shape:
                scores.append(0.0)
            else:
                scores.append(float(np.abs(cur - prev).mean()))
            prev = cur
        return scores
    except Exception:
        return []


def detect_clicks(frames: list, timestamps: list[float], threshold: float = 6.0) -> list[dict[str, Any]]:
    """Frames whose motion exceeds ``threshold``, as ``{timestamp, score}``."""
    scores = motion_scores(frames)
    clicks: list[dict[str, Any]] = []
    for score, ts in zip(scores, timestamps[1:], strict=False):
        if score >= threshold:
            clicks.append({"timestamp": round(float(ts), 2), "score": round(score, 2)})
    return clicks
