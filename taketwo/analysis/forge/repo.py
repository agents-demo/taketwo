"""Local repository access: clone, search, blame, read.

Git is called through subprocess; a missing repo/git degrades to empty results
rather than raising, so a run never dies on infrastructure.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from taketwo.storage import runtime


def _run(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=120)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except Exception as exc:
        return 1, str(exc)


def clone(repo: str, dest: str | Path, base_branch: str = "main", depth: int = 1) -> Path:
    """Shallow-clone ``owner/name`` into ``dest`` (idempotent: reuses an existing clone)."""
    dest = Path(dest)
    if (dest / ".git").exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = repo if "://" in repo else f"https://github.com/{repo}.git"
    _run(["git", "clone", "--depth", str(depth), "--branch", base_branch, url, str(dest)])
    return dest


def ensure_repo(repo: str, base_branch: str = "main") -> Path:
    """Clone ``repo`` into ``runtime/data/repos/<owner>__<name>`` and return the path."""
    safe = repo.replace("/", "__")
    return clone(repo, runtime.REPOS_DIR / safe, base_branch=base_branch)


def read_file(repo_dir: str | Path, rel_path: str) -> str:
    try:
        return (Path(repo_dir) / rel_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def search(repo_dir: str | Path, query: str, glob: str = "*.py") -> list[str]:
    """``path:line: text`` matches for ``query`` across ``glob`` files."""
    code, out = _run(["git", "grep", "-n", "--", query], cwd=Path(repo_dir))
    if code != 0:
        code, out = _run(["grep", "-rn", query, "--include", glob, "."], cwd=Path(repo_dir))
    return [line for line in out.splitlines() if line.strip()][:200]


def blame(repo_dir: str | Path, rel_path: str, line: int) -> str:
    """The commit line that last touched ``rel_path:line`` (empty on failure)."""
    code, out = _run(["git", "blame", "-L", f"{line},{line}", "--porcelain", rel_path], cwd=Path(repo_dir))
    if code != 0 or not out.splitlines():
        return ""
    first = out.splitlines()[0]
    return first


def apply_patch(repo_dir: str | Path, diff: str) -> bool:
    """Apply a unified diff in ``repo_dir`` (returns success)."""
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False, encoding="utf-8") as handle:
        handle.write(diff)
        patch_path = handle.name
    code, _ = _run(["git", "apply", patch_path], cwd=Path(repo_dir))
    return code == 0
