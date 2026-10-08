"""GitHub delivery: open an issue and a draft PR.

Dry-run friendly: with no token (or no PyGithub) the payload is returned instead of
posted, so the pipeline is testable offline and never fails on missing credentials.
"""

from __future__ import annotations

from typing import Any

from taketwo.pipeline.forge import auth


def _client() -> Any | None:
    if not auth.configured():
        return None
    try:
        from github import Github

        return Github(auth.token())
    except Exception:
        return None


def open_issue(repo: str, title: str, body: str) -> dict[str, Any]:
    """Open an issue; returns ``{number, url, url_dry_run}``."""
    client = _client()
    if client is None:
        return {"number": None, "url": None, "dry_run": True, "title": title}
    try:
        issue = client.get_repo(repo).create_issue(title=title, body=body)
        return {"number": issue.number, "url": issue.html_url, "dry_run": False}
    except Exception as exc:
        return {"number": None, "url": None, "dry_run": True, "error": str(exc)}


def open_pr(repo: str, branch: str, title: str, body: str, base: str = "main") -> dict[str, Any]:
    """Open a *draft* PR from ``branch`` into ``base`` (never merges)."""
    client = _client()
    if client is None:
        return {"number": None, "url": None, "dry_run": True, "title": title}
    try:
        pr = client.get_repo(repo).create_pull_request(title=title, body=body, head=branch, base=base, draft=True)
        return {"number": pr.number, "url": pr.html_url, "dry_run": False}
    except Exception as exc:
        return {"number": None, "url": None, "dry_run": True, "error": str(exc)}
