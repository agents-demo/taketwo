"""HTTP API: submit recordings, track jobs, read runs/scoreboard, serve media + the web app.

    uvicorn taketwo.interfaces.api:app
    # then open http://localhost:8000/app/
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
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

# Uploaded recordings are saved under runtime/data/uploads/<id>/<name>; the pipeline
# then consumes the returned server-side path like any other clip.
_ACCEPTED = {".mp4", ".mov", ".webm", ".mkv", ".png", ".jpg", ".jpeg", ".webp"}
_UPLOADS = runtime.DATA_DIR / "uploads"

# Serve the bundled sample app so "Try the sample" works end-to-end from the browser.
_SAMPLE_APP = runtime.PROJECT_ROOT / "examples" / "sample_app"
if _SAMPLE_APP.is_dir():
    app.mount("/sampleapp", StaticFiles(directory=str(_SAMPLE_APP), html=True), name="sampleapp")


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


@app.post("/upload")
def upload(file: UploadFile = File(...)) -> dict:
    """Save an uploaded recording and return its server-side path (for ``/replay/async``)."""
    setup()
    name = Path(file.filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in _ACCEPTED:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {suffix or 'unknown'}")
    dest_dir = _UPLOADS / uuid.uuid4().hex[:12]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (name or f"clip{suffix}")
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"path": str(dest), "name": dest.name}


@app.get("/sample")
def sample(request: Request) -> dict:
    """Paths for the one-tap sample: the bundled clip and the served sample app URL."""
    clip = runtime.DATA_DIR / "sample_bug_live.mov"
    if not clip.exists():
        clip = runtime.DATA_DIR / "sample_bug.mov"
    app_url = f"{str(request.base_url).rstrip('/')}/sampleapp/" if _SAMPLE_APP.is_dir() else ""
    return {"clip": str(clip) if clip.exists() else "", "app_url": app_url}


@app.get("/jobs")
def jobs() -> dict:
    """All known jobs (for the live "in flight" count)."""
    from taketwo.interfaces.runner import get_runner

    return {"jobs": get_runner().jobs()}


@app.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    from taketwo.interfaces.runner import get_runner

    status = get_runner().status(job_id)
    if status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="unknown job")
    return status


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    """Cancel a queued/running job."""
    from taketwo.interfaces.runner import get_runner

    return {"cancelled": get_runner().cancel(job_id)}


@app.post("/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    """Requeue a known job with the same parameters."""
    from taketwo.interfaces.runner import get_runner

    new_id = get_runner().retry(job_id)
    if new_id is None:
        raise HTTPException(status_code=404, detail="unknown job")
    return {"job_id": new_id, "status_url": f"/jobs/{new_id}"}


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
def review(job: str, decision: str, note: str = "", actor: str = "web") -> dict:
    from taketwo.interfaces import runs as runs_mod
    from taketwo.storage import store

    if decision not in ("approved", "changes_requested", "pending"):
        raise HTTPException(status_code=400, detail="invalid decision")
    if runs_mod.get_run(job) is None:
        raise HTTPException(status_code=404, detail="unknown run")
    store.set_review(job, decision, note, actor=actor or "web")
    return store.get_review(job)


@app.get("/media/{job}/{name}")
def media(job: str, name: str) -> FileResponse:
    """Serve a run's proof artifact (video/still); names are validated (no traversal)."""
    if "/" in name or "\\" in name or name in ("", ".", ".."):
        raise HTTPException(status_code=400, detail="invalid name")
    path = runtime.ARTIFACTS_DIR / job / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="not found")
    # Artifacts are regenerated in place; never let the browser cache a stale copy.
    return FileResponse(path, headers={"Cache-Control": "no-store, max-age=0"})


@app.get("/cards/score")
def card_score() -> Response:
    """The branded score card PNG (reproduce rate + counts)."""
    from taketwo.interfaces import runs as runs_mod
    from taketwo.reporting import share_card

    png = share_card(runs_mod.list_runs())
    if not png:
        raise HTTPException(status_code=404, detail="no runs")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get("/cards/{job}/proof")
def card_proof(job: str) -> Response:
    """The post-ready proof card PNG (before | after + verdict)."""
    from taketwo.interfaces import runs as runs_mod
    from taketwo.reporting import proof_card

    if runs_mod.get_run(job) is None:
        raise HTTPException(status_code=404, detail="unknown run")
    png = proof_card(job)
    if not png:
        raise HTTPException(status_code=404, detail="no proof image")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})


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
