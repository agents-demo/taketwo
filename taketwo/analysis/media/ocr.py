"""OCR of visible labels (so steps can be grounded in text, not pixels).

pytesseract is optional; when missing, :func:`labels` returns an empty list.
"""

from __future__ import annotations

from typing import Any


def labels(frame: Any, lang: str = "eng") -> list[str]:
    """Distinct text lines visible in one frame (empty when OCR is unavailable)."""
    try:
        import pytesseract  # type: ignore
        from PIL import Image

        image = frame if isinstance(frame, Image.Image) else Image.fromarray(frame)
        text = pytesseract.image_to_string(image, lang=lang)
        return [line.strip() for line in text.splitlines() if line.strip()]
    except Exception:
        return []


def labels_for(frames: list, lang: str = "eng") -> list[list[str]]:
    return [labels(frame, lang=lang) for frame in frames]
