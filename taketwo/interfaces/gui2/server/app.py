"""HTTP server for gui2: submit recordings, track jobs, read runs/scoreboard, serve media + the SPA.

    uvicorn taketwo.interfaces.gui2:app
    # then open http://localhost:8000/gui2/
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from taketwo.interfaces.gui2.server import config
from taketwo.interfaces.gui2.server.routes import ingest, jobs, media, replay, runs

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

# Serve the bundled sample app so "Try the sample" works end-to-end from the browser.
if config.SAMPLE_APP.is_dir():
    app.mount("/sampleapp", StaticFiles(directory=str(config.SAMPLE_APP), html=True), name="sampleapp")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


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
