"""HTTP API: submit a recording and receive the reproduction (plus a webhook stub).

    uvicorn taketwo.interfaces.api:app
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from taketwo.bootstrap import setup

app = FastAPI(title="taketwo")


class ReproduceRequest(BaseModel):
    video_path: str
    repo: str = ""
    base_branch: str = "main"
    app_url: str = ""
    agentic: bool = False


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/reproduce")
def reproduce(request: ReproduceRequest) -> dict:
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


@app.post("/webhook")
def webhook(payload: dict) -> dict:
    """GitHub webhook entry point (the sandboxed runner consumes the queue)."""
    return {"accepted": True, "event": payload.get("action", "unknown")}
