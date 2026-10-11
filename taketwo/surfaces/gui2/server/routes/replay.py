"""Run submission: synchronous and queued replay."""

from __future__ import annotations

from fastapi import APIRouter

from taketwo.core.bootstrap import setup
from taketwo.surfaces.gui2.server.models import ReplayRequest

router = APIRouter()


@router.post("/replay")
def replay(request: ReplayRequest) -> dict:
    """Run a reproduction synchronously and return the outcome."""
    from taketwo.core import service

    setup()
    try:
        outcome = service.replay_video_sync(
            request.video_path,
            repo=request.repo,
            base_branch=request.base_branch,
            app_url=request.app_url,
            agentic=request.agentic,
        )
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    return {
        "job": outcome.get("job"),
        "reproduction": outcome.get("reproduction"),
        "fix": outcome.get("fix"),
        "proof": outcome.get("proof"),
        "delivery": outcome.get("delivery"),
        "summary_path": outcome.get("summary_path"),
    }


@router.post("/replay/async")
def replay_async(request: ReplayRequest) -> dict:
    """Enqueue a reproduction in the sandboxed runner; poll it at ``/jobs/{id}``."""
    setup()
    from taketwo.core.jobs import get_runner

    job_id = get_runner().submit(
        video_path=request.video_path,
        repo=request.repo,
        base_branch=request.base_branch,
        app_url=request.app_url,
        agentic=request.agentic,
    )
    return {"job_id": job_id, "status_url": f"/jobs/{job_id}"}
