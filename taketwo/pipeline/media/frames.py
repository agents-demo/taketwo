"""Frame extraction from a video (or a single still image).

imageio/Pillow are optional: when missing, :func:`sample_frames` returns no frames
and the caller degrades gracefully.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def load_image(path: str | Path) -> tuple[dict[str, Any], list, list[float]]:
    """A still image as a one-frame clip: ``(meta, frames, timestamps)``."""
    meta: dict[str, Any] = {"path": str(path), "kind": "image"}
    try:
        from PIL import Image

        frame = Image.open(path).convert("RGB")
        meta["size"] = list(frame.size)
        return meta, [frame], [0.0]
    except Exception:
        return meta, [], []


def sample_frames(
    video_path: str | Path,
    fps: float = 2.0,
    max_frames: int = 12,
) -> tuple[dict[str, Any], list, list[float]]:
    """Sample up to ``max_frames`` frames at ``fps`` from ``video_path``.

    Returns ``(meta, frames, timestamps)``; an empty frame list means the clip could
    not be read (missing codec, missing optional dependency).
    """
    if is_image(video_path):
        return load_image(video_path)

    meta: dict[str, Any] = {"path": str(video_path), "kind": "video"}
    try:
        import imageio.v3 as iio

        frames: list = []
        timestamps: list[float] = []
        step = max(1, int(round(1.0 / max(fps, 0.01))))
        for i, frame in enumerate(iio.imiter(video_path)):
            if i % step == 0:
                frames.append(frame)
                timestamps.append(i / max(fps, 0.01))
            if len(frames) >= max_frames:
                break
        meta["frames"] = len(frames)
        return meta, frames, timestamps
    except Exception as exc:  # pragma: no cover - depends on codecs
        meta["error"] = str(exc)
        return meta, [], []
