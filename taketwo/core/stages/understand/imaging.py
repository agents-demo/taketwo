"""Image compositing for the understand stage: the contact sheet the vision agent reads.

Best-effort: returns ``None`` when Pillow is absent.
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
