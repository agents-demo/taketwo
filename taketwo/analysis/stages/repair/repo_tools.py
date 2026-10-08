"""Plain-callable repo tools for the repair agent (the backend decorates them)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from taketwo.analysis.forge import repo as forge_repo


def make_tools(repo_dir: str | Path) -> list[Callable]:
    """Tools bound to one cloned repo: search, read, blame, apply-preview."""

    def search_repo(query: str) -> str:
        """Find `query` in the repository; returns `path:line: text` matches."""
        return "\n".join(forge_repo.search(repo_dir, query)) or "(no matches)"

    def read_repo_file(path: str) -> str:
        """Read a repository file by relative path."""
        return forge_repo.read_file(repo_dir, path) or "(not found)"

    def blame_line(path: str, line: int) -> str:
        """The commit that last touched `path:line`."""
        return forge_repo.blame(repo_dir, path, line) or "(no blame)"

    return [search_repo, read_repo_file, blame_line]
