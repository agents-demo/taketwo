"""HTTP API: submit recordings, track jobs, read runs/scoreboard, serve media + the web app.

    uvicorn taketwo.interfaces.api:app
    # then open http://localhost:8000/app/
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from taketwo.bootstrap import setup
from taketwo.pipeline.forge import auth as forge_auth
from taketwo.pipeline.forge import verify_signature
from taketwo.storage import runtime

app = FastAPI(title="TakeTwo")

# Allow the SvelteKit dev server (5173) to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_HERE = Path(__file__).resolve().parent
_APP = _HERE / "app" / "build"  # the SvelteKit app (built static assets)


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


@app.get("/runs")
def runs() -> dict:
    from taketwo.interfaces import runs as runs_mod

    return {"runs": runs_mod.list_runs()}


@app.get("/runs/{job}")
def run(job: str) -> dict:
    from taketwo.interfaces import runs as runs_mod

    found = runs_mod.get_run(job)
    if found is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return found


@app.get("/scoreboard")
def scoreboard() -> dict:
    from taketwo.interfaces import runs as runs_mod

    return runs_mod.scoreboard()


@app.get("/runs/{job}/ask")
def ask(job: str, q: str) -> dict:
    from taketwo.interfaces import runs as runs_mod
    from taketwo.interfaces import service

    if not q.strip():
        raise HTTPException(status_code=400, detail="empty question")
    if runs_mod.get_run(job) is None:
        raise HTTPException(status_code=404, detail="unknown run")
    setup()
    return {"answer": service.ask_sync(job, q)}


@app.post("/runs/{job}/review/{decision}")
def review(job: str, decision: str, note: str = "") -> dict:
    from taketwo.interfaces import runs as runs_mod
    from taketwo.storage import store

    if decision not in ("approved", "changes_requested", "pending"):
        raise HTTPException(status_code=400, detail="invalid decision")
    if runs_mod.get_run(job) is None:
        raise HTTPException(status_code=404, detail="unknown run")
    store.set_review(job, decision, note, actor="web")
    return store.get_review(job)


@app.get("/media/{job}/{name}")
def media(job: str, name: str) -> FileResponse:
    """Serve a run's proof artifact (video/still); names are validated (no traversal)."""
    if "/" in name or "\\" in name or name in ("", ".", ".."):
        raise HTTPException(status_code=400, detail="invalid name")
    path = runtime.ARTIFACTS_DIR / job / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path)


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


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/app/" if _APP.exists() else "/health")


@app.get("/app/{path:path}")
@app.get("/app")
def spa(path: str = "") -> FileResponse:
    """Serve the built SvelteKit app, falling back to index.html for client routes."""
    root = _APP.resolve()
    candidate = (root / path).resolve()
    if path and candidate.is_file() and str(candidate).startswith(str(root)):
        return FileResponse(candidate)
    return FileResponse(root / "index.html")
