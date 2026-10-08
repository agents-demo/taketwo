"""GitHub delivery: open an issue and a draft PR.

Dry-run friendly: with no token (or no PyGithub) the payload is returned instead of
posted, so the pipeline is testable offline and never fails on missing credentials.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from taketwo.pipeline.forge import auth


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    """Verify a GitHub webhook ``X-Hub-Signature-256`` over the raw body.

    With no secret configured the webhook is accepted (dev mode); with a secret and a
    missing/incorrect signature it is rejected.
    """
    if not secret:
        return True
    if not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


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
