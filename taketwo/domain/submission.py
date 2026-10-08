"""The submission: what the reporter gave us and where to reproduce it.

Pure. Operates on plain dicts so it stays dependency-free.
"""

from __future__ import annotations

import re
from typing import Any

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def normalize(data: dict[str, Any] | None) -> dict[str, Any]:
    """Coerce a submission into the canonical shape."""
    data = data or {}
    return {
        "video_path": str(data.get("video_path", "") or ""),
        "repo": str(data.get("repo", "") or "").strip("/"),
        "base_branch": str(data.get("base_branch", "main") or "main"),
        "app_url": str(data.get("app_url", "") or ""),
    }


def validate(submission: dict[str, Any]) -> list[str]:
    """Return the list of problems with a submission (empty = valid)."""
    problems: list[str] = []
    if not submission.get("video_path"):
        problems.append("video_path is required")
    if submission.get("repo") and "/" not in submission["repo"]:
        problems.append("repo must be 'owner/name'")
    return problems


def slug(text: str) -> str:
    """A filesystem-safe token from arbitrary text."""
    return _SAFE.sub("-", text).strip("-") or "job"


def job_id(submission: dict[str, Any]) -> str:
    """Stable id for a submission: ``owner__name@branch`` or the video stem."""
    repo = submission.get("repo") or ""
    if repo:
        return slug(repo.replace("/", "__")) + "@" + slug(submission.get("base_branch") or "main")
    stem = str(submission.get("video_path", "")).rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    stem = stem.rsplit(".", 1)[0]
    return slug(stem)
