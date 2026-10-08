"""Local repository access: clone, search, blame, read, and publish a branch.

Git is called through subprocess; a missing repo/git degrades to empty results
rather than raising, so a run never dies on infrastructure. Commits use bot
identity from the environment (never the user's git config).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from taketwo.forge import auth
from taketwo.storage import runtime

BOT_NAME = "TakeTwo Bot"
BOT_EMAIL = "taketwo@users.noreply.github.com"


def _identity_env() -> dict[str, str]:
    return {
        "GIT_AUTHOR_NAME": BOT_NAME,
        "GIT_AUTHOR_EMAIL": BOT_EMAIL,
        "GIT_COMMITTER_NAME": BOT_NAME,
        "GIT_COMMITTER_EMAIL": BOT_EMAIL,
    }


def _run(args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> tuple[int, str]:
    full_env = {**os.environ, **(env or {})}
    try:
        proc = subprocess.run(
            args, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=120, env=full_env
        )
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


def run_tests(repo_dir: str | Path, command: str, timeout: int = 600) -> dict:
    """Run ``command`` in ``repo_dir``; returns ``{ran, passed, output}``."""
    if not command:
        return {"ran": False, "passed": False, "output": ""}
    try:
        proc = subprocess.run(
            command, cwd=str(repo_dir), shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {"ran": True, "passed": proc.returncode == 0, "output": (proc.stdout or "") + (proc.stderr or "")}
    except Exception as exc:
        return {"ran": False, "passed": False, "output": str(exc)}


def run_tests_on_patch(repo: str, base_branch: str, diff: str, command: str) -> dict:
    """Check out the base, apply ``diff``, run ``command``, then leave the tree clean."""
    if not repo or not command:
        return {"ran": False, "passed": False, "output": ""}
    try:
        repo_dir = ensure_repo(repo, base_branch)
        _run(["git", "checkout", "-f", base_branch], cwd=repo_dir)
        _run(["git", "reset", "--hard", "HEAD"], cwd=repo_dir)
        if diff and not apply_patch(repo_dir, diff):
            return {"ran": False, "passed": False, "output": "patch did not apply"}
        return run_tests(repo_dir, command)
    except Exception as exc:
        return {"ran": False, "passed": False, "output": str(exc)}


def _rev_parse(repo_dir: str | Path) -> str:
    code, out = _run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(repo_dir))
    return out.strip().splitlines()[0] if code == 0 and out.strip() else ""


def _token_url(repo: str) -> str:
    token = auth.token()
    return f"https://x-access-token:{token}@github.com/{repo}.git" if repo and token else ""


def publish_branch(
    repo_dir: str | Path,
    branch: str,
    diff: str,
    message: str,
    repo: str = "",
) -> dict:
    """Apply ``diff`` on a fresh ``branch``, commit it, and push when a token exists.

    Returns ``{branch, commit, pushed, dry_run}``; ``pushed`` is ``False`` (dry-run)
    when no GitHub token is configured, so the pipeline works fully offline.
    """
    repo_dir = Path(repo_dir)
    if not (repo_dir / ".git").exists():
        return {"branch": branch, "commit": "", "pushed": False, "error": "not a git repository"}

    env = _identity_env()
    code, out = _run(["git", "checkout", "-B", branch], cwd=repo_dir, env=env)
    if code != 0:
        return {"branch": branch, "commit": "", "pushed": False, "error": out.strip()[:200]}

    if diff and not apply_patch(repo_dir, diff):
        return {"branch": branch, "commit": "", "pushed": False, "error": "patch did not apply"}

    _run(["git", "add", "-A"], cwd=repo_dir, env=env)
    code, out = _run(["git", "commit", "-m", message or "fix: reproduce scenario"], cwd=repo_dir, env=env)
    commit = _rev_parse(repo_dir)
    if code != 0:
        return {"branch": branch, "commit": commit, "pushed": False, "error": out.strip()[:200]}

    url = _token_url(repo)
    pushed = False
    if url:
        code, _ = _run(["git", "push", "-u", url, f"{branch}:{branch}"], cwd=repo_dir, env=env)
        pushed = code == 0
    return {"branch": branch, "commit": commit, "pushed": pushed, "dry_run": not url}
