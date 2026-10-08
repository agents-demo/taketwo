"""Shared forge primitives: local repo access and GitHub delivery.

Used by 2+ stages (``repair`` searches/blames; ``deliver`` opens the issue/PR). A
small façade so stages never touch git or PyGithub directly.
"""

from taketwo.pipeline.forge.github import open_issue, open_pr, verify_signature
from taketwo.pipeline.forge.repo import (
    apply_patch,
    blame,
    clone,
    ensure_repo,
    publish_branch,
    read_file,
    reset,
    run_tests,
    run_tests_on_patch,
    search,
)

__all__ = [
    "apply_patch",
    "blame",
    "clone",
    "ensure_repo",
    "open_issue",
    "open_pr",
    "publish_branch",
    "read_file",
    "reset",
    "run_tests",
    "run_tests_on_patch",
    "search",
    "verify_signature",
]
