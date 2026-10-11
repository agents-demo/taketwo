"""Proof media and share cards."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from taketwo.integrations.reporting import proof_card, share_card
from taketwo.integrations.storage import runtime
from taketwo.surfaces.gui2.server import runs as read_model

router = APIRouter()


@router.get("/media/{job}/{name}")
def media(job: str, name: str) -> FileResponse:
    """Serve a run's proof artifact (video/still); names are validated (no traversal)."""
    if "/" in name or "\\" in name or name in ("", ".", ".."):
        raise HTTPException(status_code=400, detail="invalid name")
    path = runtime.ARTIFACTS_DIR / job / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="not found")
    # Artifacts are regenerated in place; never let the browser cache a stale copy.
    return FileResponse(path, headers={"Cache-Control": "no-store, max-age=0"})


@router.get("/cards/score")
def card_score() -> Response:
    """The branded score card PNG (reproduce rate + counts)."""
    png = share_card(read_model.list_runs())
    if not png:
        raise HTTPException(status_code=404, detail="no runs")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get("/cards/{job}/proof")
def card_proof(job: str) -> Response:
    """The post-ready proof card PNG (before | after + verdict)."""
    if read_model.get_run(job) is None:
        raise HTTPException(status_code=404, detail="unknown run")
    png = proof_card(job)
    if not png:
        raise HTTPException(status_code=404, detail="no proof image")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})
