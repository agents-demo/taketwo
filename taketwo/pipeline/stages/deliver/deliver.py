"""Stage: write the issue/PR files and open them on the forge (draft PR only)."""

from __future__ import annotations

from typing import Any

from taketwo import reporting
from taketwo.domain import render
from taketwo.domain.submission import job_id
from taketwo.pipeline.forge import ensure_repo, open_issue, open_pr, publish_branch
from taketwo.pipeline.progress import Progress, tick


def deliver(
    submission: dict[str, Any],
    reproduction: dict[str, Any],
    fix: dict[str, Any],
    proof: dict[str, Any],
    progress: Progress | None = None,
) -> dict[str, Any]:
    """Render the artifacts and (when verified) open an issue + draft PR."""
    tick(progress, "delivering", 97)
    exports = reporting.write(submission, reproduction, fix, proof)
    out: dict[str, Any] = {"exports": exports}

    repo = submission.get("repo", "")
    verified = bool((proof or {}).get("verification", {}).get("ok"))
    if not repo or not fix.get("diff") or not verified:
        return out

    job = job_id(submission)
    title = f"[TakeTwo] {fix.get('summary') or 'fix a reproduced bug'}"
    branch = f"taketwo/{job}"
    repo_dir = ensure_repo(repo, submission.get("base_branch", "main"))
    out["branch"] = publish_branch(repo_dir, branch=branch, diff=fix["diff"], message=title, repo=repo)
    out["issue"] = open_issue(repo, title, render.issue_markdown(submission, reproduction))
    out["pr"] = open_pr(
        repo,
        branch=branch,
        title=title,
        body=render.pr_markdown(submission, reproduction, fix, proof),
        base=submission.get("base_branch", "main"),
    )
    return out
