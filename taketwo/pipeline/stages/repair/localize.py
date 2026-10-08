"""Cheap localization: evidence strings + console stack frames → repo culprits."""

from __future__ import annotations

import re
from pathlib import Path

from taketwo.pipeline.forge import repo as forge_repo

# Python tracebacks (File "x.py", line N) and JS/URL frames (app.js:12:5).
_PATTERNS = (
    re.compile(r'File "([^"]+)", line (\d+)'),
    re.compile(r"([\w./\\-]+\.(?:js|mjs|ts|tsx|jsx|py|rb|go|java|php)):(\d+)(?::\d+)?"),
)


def _queries(reproduction: dict) -> list[str]:
    queries: list[str] = []
    summary = reproduction.get("evidence", {}).get("summary", "")
    if summary:
        queries.append(summary.split(":")[-1].strip()[:80])
    for step in reproduction.get("steps", []):
        if step.get("target"):
            queries.append(step["target"])
    return [q for q in queries if q][:5]


def _console_frames(reproduction: dict) -> list[tuple[str, int]]:
    """``(basename, line)`` pairs parsed from the captured console/stack frames."""
    frames: list[tuple[str, int]] = []
    for line in reproduction.get("evidence", {}).get("console") or []:
        for pattern in _PATTERNS:
            for match in pattern.finditer(line):
                raw = match.group(1)
                name = raw.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                frames.append((name, int(match.group(2))))
    return frames[:5]


def _console_hits(repo_dir: str | Path, reproduction: dict) -> list[str]:
    """Locate the parsed stack-frame files in the repo."""
    hits: list[str] = []
    for name, line in _console_frames(reproduction):
        for match in forge_repo.search(repo_dir, name)[:2]:
            hits.append(f"{match}  (console {name}:{line})")
    return hits


def localize(repo_dir: str | Path, reproduction: dict) -> list[str]:
    """Return candidate ``path:line: text`` culprits for the reproduction."""
    found: list[str] = []
    for query in _queries(reproduction):
        found.extend(forge_repo.search(repo_dir, query))
    found.extend(_console_hits(repo_dir, reproduction))

    seen: set[str] = set()
    unique: list[str] = []
    for line in found:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return unique[:20]
