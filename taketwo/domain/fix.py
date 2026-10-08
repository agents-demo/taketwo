"""The proposed fix: a patch, the files it touches, and a regression test.

Pure. A fix is ``{"summary", "files", "diff", "test", "culprits"}``.
"""

from __future__ import annotations

from typing import Any


def normalize(data: dict[str, Any] | None) -> dict[str, Any]:
    data = data or {}
    return {
        "summary": str(data.get("summary", "") or ""),
        "files": [str(x) for x in data.get("files", []) or []],
        "diff": str(data.get("diff", "") or ""),
        "test": str(data.get("test", "") or ""),
        "culprits": [str(x) for x in data.get("culprits", []) or []],
    }


def validate(fix: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if not fix.get("diff"):
        problems.append("fix has no diff")
    if not fix.get("test"):
        problems.append("fix has no regression test")
    return problems
