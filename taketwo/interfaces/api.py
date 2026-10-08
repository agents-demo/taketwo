"""HTTP API: submit a recording, track the job, and receive verified webhooks.

    uvicorn taketwo.interfaces.api:app
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from taketwo.bootstrap import setup
from taketwo.pipeline.forge import auth as forge_auth
from taketwo.pipeline.forge import verify_signature

app = FastAPI(title="TakeTwo")


class ReplayRequest(BaseModel):
    video_path: str
    repo: str = ""
    base_branch: str = "main"
    app_url: str = ""
    agentic: bool = False


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/replay")
def replay(request: ReplayRequest) -> dict:
    """Run a reproduction synchronously and return the outcome."""
    from taketwo.interfaces import service

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


@app.post("/replay/async")
def replay_async(request: ReplayRequest) -> dict:
    """Enqueue a reproduction in the sandboxed runner; poll it at ``/jobs/{id}``."""
    setup()
    from taketwo.interfaces.runner import get_runner

    job_id = get_runner().submit(
        video_path=request.video_path,
        repo=request.repo,
        base_branch=request.base_branch,
        app_url=request.app_url,
        agentic=request.agentic,
    )
    return {"job_id": job_id, "status_url": f"/jobs/{job_id}"}


@app.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    from taketwo.interfaces.runner import get_runner

    status = get_runner().status(job_id)
    if status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="unknown job")
    return status


@app.post("/webhook")
async def webhook(request: Request) -> dict:
    """GitHub webhook: verify the HMAC signature, then accept (or enqueue) the event."""
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")
    if not verify_signature(forge_auth.webhook_secret(), body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    import json

    try:
        payload = json.loads(body or b"{}")
    except Exception:
        payload = {}

    video_path = payload.get("video_path", "")
    if video_path:
        setup()
        from taketwo.interfaces.runner import get_runner

        job_id = get_runner().submit(video_path=video_path, repo=payload.get("repo", ""))
        return {"accepted": True, "job_id": job_id}
    return {"accepted": True, "event": payload.get("action", "unknown")}
