"""Model-call I/O tracing: the input messages and output text of every call (with images)."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from taketwo.integrations.agents.telemetry.sanitize import (
    _clip,
    _iter_image_urls,
    _tool_calls,
    sanitize_messages,
)


class CallTrace:
    """Records the input messages and output text of every model call."""

    def __init__(self, record_io: bool = True, media_dir: Path | None = None) -> None:
        self.calls: list[dict] = []
        self.record_io = record_io
        self.media_dir = media_dir

    def _save_images(self, stem: str, messages: Any) -> list[str]:
        if self.media_dir is None:
            return []
        paths: list[str] = []
        try:
            self.media_dir.mkdir(parents=True, exist_ok=True)
            for i, url in enumerate(_iter_image_urls(messages), start=1):
                header, _, payload = url.partition(";base64,")
                ext = "png" if "png" in header else ("jpg" if ("jpeg" in header or "jpg" in header) else "bin")
                path = self.media_dir / f"{stem}_img{i}.{ext}"
                path.write_bytes(base64.b64decode(payload))
                paths.append(str(path))
        except Exception:
            return paths
        return paths

    def capture(
        self,
        label: str,
        messages: Any,
        output: Any,
        model: str = "",
        tools: Any = None,
        usage: dict | None = None,
        started: float = 0.0,
        seq: int = 0,
        seconds: float = 0.0,
        requested: Any = None,
    ) -> None:
        try:
            entry = {
                "label": label,
                "model": model,
                "started": started,
                "seq": seq,
                "seconds": seconds,
                "input": sanitize_messages(messages, limit=None) if self.record_io else [],
                "output": _clip(output, None) if self.record_io else "",
            }
            if tools:
                entry["tools"] = [str(getattr(t, "name", t)) for t in tools]
            if requested:
                entry["requested"] = _tool_calls(requested)
            for key in ("prompt_tokens", "completion_tokens", "cached_tokens", "total_tokens"):
                if usage and usage.get(key) is not None:
                    entry[key] = int(usage.get(key) or 0)
            if self.record_io and self.media_dir is not None:
                images = self._save_images(f"call{seq or len(self.calls) + 1}", messages)
                if images:
                    entry["images"] = images
            self.calls.append(entry)
        except Exception:
            pass
