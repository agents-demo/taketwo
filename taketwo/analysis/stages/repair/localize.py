"""Cheap localization: search the repo for the evidence strings."""

from __future__ import annotations

from pathlib import Path

from taketwo.analysis.forge import repo as forge_repo


def _queries(reproduction: dict) -> list[str]:
    queries: list[str] = []
    summary = reproduction.get("evidence", {}).get("summary", "")
    if summary:
        queries.append(summary.split(":")[-1].strip()[:80])
    for step in reproduction.get("steps", []):
        if step.get("target"):
            queries.append(step["target"])
    return [q for q in queries if q][:5]


def localize(repo_dir: str | Path, reproduction: dict) -> list[str]:
    """Return candidate ``path:line: text`` culprits for the reproduction."""
    found: list[str] = []
    for query in _queries(reproduction):
        found.extend(forge_repo.search(repo_dir, query))
    seen: set[str] = set()
    unique: list[str] = []
    for line in found:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return unique[:20]
