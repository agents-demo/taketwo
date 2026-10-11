"""Before/after proof composition: the labelled ``[before | after]`` image and video.

Best-effort: returns ``None`` when Pillow/imageio are absent.
"""

from __future__ import annotations

from pathlib import Path

_CAPTIONS = (("before", (255, 90, 90)), ("after", (120, 255, 120)))


def _side_by_side(before: str | Path, after: str | Path):
    """The composed PIL image of ``[before | after]`` (or ``None``)."""
    try:
        from PIL import Image, ImageDraw

        left = Image.open(before).convert("RGB")
        right = Image.open(after).convert("RGB")
        height = max(left.height, right.height)
        canvas = Image.new("RGB", (left.width + right.width, height), (0, 0, 0))
        canvas.paste(left, (0, 0))
        canvas.paste(right, (left.width, 0))
        draw = ImageDraw.Draw(canvas)
        for (text, colour), x in zip(_CAPTIONS, (0, left.width), strict=False):
            draw.rectangle([x, 0, x + 80, 18], fill=(0, 0, 0))
            draw.text((x + 6, 4), text, fill=colour)
        return canvas
    except Exception:
        return None


def proof(before: str, after: str, out_path: str) -> str | None:
    """Return the path to a labelled ``[before | after]`` image (or ``None``)."""
    if not before or not after:
        return None
    canvas = _side_by_side(before, after)
    if canvas is None:
        return None
    try:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out)
        return str(out)
    except Exception:
        return None


def proof_video(before: str, after: str, out_path: str, fps: float = 4.0, seconds: float = 2.0) -> str | None:
    """Return the path to a labelled ``[before | after]`` mp4 (or ``None``)."""
    if not before or not after:
        return None
    canvas = _side_by_side(before, after)
    if canvas is None:
        return None
    try:
        import imageio.v2 as iio
        import numpy as np

        frame = np.asarray(canvas)
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with iio.get_writer(str(out), fps=max(fps, 1.0)) as writer:
            for _ in range(max(1, int(fps * seconds))):
                writer.append_data(frame)
        return str(out)
    except Exception:
        return None
