"""Outbound artifacts: render a reproduction's issue and PR text to disk.

Pure rendering lives in :mod:`taketwo.domain.render`; this module only decides where
the files go (``runtime/data/exports/``).
"""

from __future__ import annotations

from pathlib import Path

from taketwo.domain import render
from taketwo.storage import runtime


def write(submission: dict, reproduction: dict, fix: dict | None = None, proof: dict | None = None) -> dict[str, str]:
    """Render and write ``issue.md`` (+ ``pr.md``) for a job; return {kind: path}."""
    exports = runtime.DATA_DIR / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    job = render.job_id(submission)

    written: dict[str, str] = {}
    issue_path = exports / f"{job}_issue.md"
    issue_path.write_text(render.issue_markdown(submission, reproduction), encoding="utf-8")
    written["issue"] = str(issue_path)

    if fix:
        pr_path = exports / f"{job}_pr.md"
        pr_path.write_text(render.pr_markdown(submission, reproduction, fix, proof or {}), encoding="utf-8")
        written["pr"] = str(pr_path)

    return written


def proof_dir() -> Path:
    """Directory holding the before/after clips for a job."""
    path = runtime.ARTIFACTS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path
