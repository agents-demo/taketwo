"""HTTP server for gui2: submit recordings, track jobs, read runs/scoreboard, serve media + the SPA.

    uvicorn taketwo.surfaces.gui2:app
    # then open http://localhost:8000/gui2/
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from taketwo.surfaces.gui2.server import config
from taketwo.surfaces.gui2.server.routes import ingest, jobs, media, replay, runs
from taketwo.surfaces.readiness import checks as readiness_checks

app = FastAPI(title="TakeTwo")

# Allow the SvelteKit dev server (5173) to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(replay.router)
app.include_router(jobs.router)
app.include_router(runs.router)
app.include_router(media.router)
app.include_router(ingest.router)

# Serve the bundled demo apps so the in-browser demo picker works end-to-end.
if config.SCENARIOS_DIR.is_dir():
    app.mount("/demoapps", StaticFiles(directory=str(config.SCENARIOS_DIR), html=True), name="demoapps")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/ready")
def ready() -> dict:
    """Environment readiness (model / browser / delivery / sample) for the UI."""
    return {"checks": readiness_checks()}


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/gui2/" if config.CLIENT_BUILD.exists() else "/health")


@app.get("/gui2/{path:path}")
@app.get("/gui2")
def spa(path: str = "") -> FileResponse:
    """Serve the built gui2 SPA, falling back to index.html for client routes."""
    root = config.CLIENT_BUILD.resolve()
    candidate = (root / path).resolve()
    if path and candidate.is_file() and str(candidate).startswith(str(root)):
        return FileResponse(candidate)
    return FileResponse(root / "index.html")
