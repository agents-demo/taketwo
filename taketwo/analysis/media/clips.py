"""Clip compositing: contact sheets, before/after stitching, video writing.

Every helper is best-effort and returns ``None`` when Pillow/imageio are absent, so
the pipeline keeps its structure without the media extras.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def contact_sheet(frames: list, timestamps: list[float], cols: int = 4, cell: tuple[int, int] = (320, 180)) -> Any:
    """A grid of frames labelled with their timestamps (or ``None``)."""
    try:
        import math

        from PIL import Image, ImageDraw

        if not frames:
            return None
        rows = math.ceil(len(frames) / cols)
        sheet = Image.new("RGB", (cols * cell[0], rows * cell[1]), (18, 18, 22))
        draw = ImageDraw.Draw(sheet)
        for i, frame in enumerate(frames):
            r, c = divmod(i, cols)
            thumb = frame.convert("RGB").resize(cell)
            sheet.paste(thumb, (c * cell[0], r * cell[1]))
            label = f"#{i + 1} t={timestamps[i]:.2f}s" if i < len(timestamps) else f"#{i + 1}"
            draw.rectangle([c * cell[0], r * cell[1], c * cell[0] + 108, r * cell[1] + 16], fill=(0, 0, 0))
            draw.text((c * cell[0] + 4, r * cell[1] + 3), label, fill=(255, 235, 60))
        return sheet
    except Exception:
        return None


def save_image(image: Any, path: str | Path) -> str | None:
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        return str(path)
    except Exception:
        return None


def stitch_side_by_side(before: str | Path, after: str | Path, out_path: str | Path, label: bool = True) -> str | None:
    """Compose two images into ``[before | after]`` and save to ``out_path``."""
    try:
        from PIL import Image, ImageDraw

        left = Image.open(before).convert("RGB")
        right = Image.open(after).convert("RGB")
        height = max(left.height, right.height)
        canvas = Image.new("RGB", (left.width + right.width, height), (0, 0, 0))
        canvas.paste(left, (0, 0))
        canvas.paste(right, (left.width, 0))
        if label:
            draw = ImageDraw.Draw(canvas)
            draw.rectangle([0, 0, 80, 18], fill=(0, 0, 0))
            draw.text((6, 4), "before", fill=(255, 90, 90))
            draw.rectangle([left.width, 0, left.width + 70, 18], fill=(0, 0, 0))
            draw.text((left.width + 6, 4), "after", fill=(120, 255, 120))
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_path)
        return str(out_path)
    except Exception:
        return None


def stitch_video(
    before: str | Path,
    after: str | Path,
    out_path: str | Path,
    fps: float = 4.0,
    seconds: float = 2.0,
) -> str | None:
    """Compose ``[before | after]`` and write a short mp4 (or ``None``)."""
    try:
        import numpy as np
        from PIL import Image, ImageDraw

        left = Image.open(before).convert("RGB")
        right = Image.open(after).convert("RGB")
        height = max(left.height, right.height)
        canvas = Image.new("RGB", (left.width + right.width, height), (0, 0, 0))
        canvas.paste(left, (0, 0))
        canvas.paste(right, (left.width, 0))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, 80, 18], fill=(0, 0, 0))
        draw.text((6, 4), "before", fill=(255, 90, 90))
        draw.rectangle([left.width, 0, left.width + 70, 18], fill=(0, 0, 0))
        draw.text((left.width + 6, 4), "after", fill=(120, 255, 120))

        frame = np.asarray(canvas)
        frames = [frame] * max(1, int(fps * seconds))
        return write_video(frames, out_path, fps=fps)
    except Exception:
        return None


def write_video(frames: list, out_path: str | Path, fps: float = 4.0) -> str | None:
    """Write frames to an mp4 (or ``None`` when imageio is unavailable)."""
    try:
        import imageio.v2 as iio

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with iio.get_writer(str(out_path), fps=max(fps, 1.0)) as writer:
            for frame in frames:
                writer.append_data(frame)
        return str(out_path)
    except Exception:
        return None
