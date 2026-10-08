"""Per-job frame/OCR cache, keyed by path + mtime + size."""

from __future__ import annotations

import hashlib
from pathlib import Path

from taketwo.storage import runtime


def job_dir(job: str) -> Path:
    path = runtime.CACHE_DIR / job
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_key(video_path: str | Path) -> str:
    """A cache key that changes when the file's content/size changes."""
    path = Path(video_path)
    try:
        stat = path.stat()
        raw = f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}"
    except OSError:
        raw = str(video_path)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
