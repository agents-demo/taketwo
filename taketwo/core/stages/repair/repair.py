"""Stage: localize + propose a fix.

If the bug was not reproduced there is nothing to fix (honest, not a guess). A
proposed patch staged at ``runtime/data/<job>_proposed.patch`` is used directly (the
deterministic demo path); otherwise the repair agent is asked to produce a diff and a
regression test.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from taketwo.core import agent_reply, scenarios
from taketwo.core.progress import Progress, tick
from taketwo.core.stages.repair import localize, prompts
from taketwo.domain import fix as fix_mod
from taketwo.integrations.forge import ensure_repo
from taketwo.integrations.storage import runtime


def _files_from_diff(diff: str) -> list[str]:
    return [line[6:] for line in diff.splitlines() if line.startswith("+++ b/")]


def _staged(job: str) -> tuple[str, str] | None:
    patch = runtime.DATA_DIR / f"{job}_proposed.patch"
    if not patch.exists():
        return None
    test = runtime.DATA_DIR / f"{job}_proposed.test"
    return patch.read_text(encoding="utf-8"), (test.read_text(encoding="utf-8") if test.exists() else "")


def _build_repo_agent(repo_dir: Path) -> Any:
    from taketwo.core.stages.repair.build_agent import build_agent

    try:
        return build_agent(repo_dir=str(repo_dir)).agent
    except Exception:
        return None


async def repair(
    reproduction: dict[str, Any],
    repo: str,
    job: str,
    progress: Progress | None = None,
    video_path: str = "",
) -> dict[str, Any]:
    """Return a normalized fix (possibly empty when nothing could be fixed)."""
    if reproduction.get("verdict") != "reproduced":
        return fix_mod.normalize({"summary": "no fix: the bug was not reproduced"})

    tick(progress, "locating the cause", 70)
    repo_dir = Path(await asyncio.to_thread(ensure_repo, repo)) if repo else None
    culprits = await asyncio.to_thread(localize.localize, repo_dir, reproduction) if repo_dir else []

    staged = _staged(job)
    if staged is not None:
        diff, test = staged
        return fix_mod.normalize(
            {
                "summary": reproduction.get("evidence", {}).get("summary") or "resolve the reproduced bug",
                "files": _files_from_diff(diff),
                "diff": diff,
                "test": test,
                "culprits": culprits,
            }
        )

    # Demo scenario without a repo: use the fix the scenario ships for its little app.
    scenario = scenarios.for_video(video_path)
    if scenario and scenario.get("patch"):
        return fix_mod.normalize(
            {
                "summary": reproduction.get("evidence", {}).get("summary") or "resolve the reproduced bug",
                "files": _files_from_diff(scenario["patch"]),
                "diff": scenario["patch"],
                "test": scenario.get("test", ""),
                "culprits": culprits,
            }
        )

    if repo_dir is not None:
        agent = _build_repo_agent(repo_dir)
        if agent is not None:
            try:
                text = await agent_reply.ask(agent, prompts.build_user(reproduction))
                data = agent_reply.extract_json(text)
                if data.get("diff"):
                    data.setdefault("culprits", culprits)
                    data.setdefault("files", _files_from_diff(str(data.get("diff", ""))))
                    return fix_mod.normalize(data)
            except Exception:
                pass

    return fix_mod.normalize({"summary": "candidate cause identified; no patch proposed", "culprits": culprits})
