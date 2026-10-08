"""Shared forge primitives: local repo access and GitHub delivery.

Used by 2+ stages (``repair`` searches/blames; ``deliver`` opens the issue/PR). A
small façade so stages never touch git or PyGithub directly.
"""

from taketwo.analysis.forge.github import open_issue, open_pr
from taketwo.analysis.forge.repo import blame, clone, ensure_repo, read_file, search

__all__ = ["blame", "clone", "ensure_repo", "open_issue", "open_pr", "read_file", "search"]
