"""Shared forge primitives: local repo access and GitHub delivery.

Used by 2+ stages (``repair`` searches/blames; ``deliver`` opens the issue/PR). A
small façade so stages never touch git or PyGithub directly.
"""

from taketwo.forge.github import open_issue, open_pr
from taketwo.forge.repo import (
    blame,
    clone,
    ensure_repo,
    publish_branch,
    read_file,
    run_tests,
    run_tests_on_patch,
    search,
)

__all__ = [
    "blame",
    "clone",
    "ensure_repo",
    "open_issue",
    "open_pr",
    "publish_branch",
    "read_file",
    "run_tests",
    "run_tests_on_patch",
    "search",
]
