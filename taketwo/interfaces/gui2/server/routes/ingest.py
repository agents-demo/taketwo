"""Ingest: upload a clip, the one-tap sample, and the GitHub webhook."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from taketwo.bootstrap import setup
from taketwo.interfaces.gui2.server import config
from taketwo.pipeline.forge import auth as forge_auth
from taketwo.pipeline.forge import verify_signature
from taketwo.storage import runtime

router = APIRouter()


@router.post("/upload")
def upload(file: UploadFile = File(...)) -> dict:  # noqa: B008  (FastAPI dependency idiom)
    """Save an uploaded recording and return its server-side path (for ``/replay/async``)."""
    setup()
    name = Path(file.filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in config.ACCEPTED:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {suffix or 'unknown'}")
    dest_dir = config.UPLOADS / uuid.uuid4().hex[:12]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (name or f"clip{suffix}")
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"path": str(dest), "name": dest.name}


@router.get("/sample")
def sample(request: Request) -> dict:
    """Paths for the one-tap sample: the bundled clip and the served sample app URL."""
    clip = runtime.DATA_DIR / "sample_bug_live.mov"
    if not clip.exists():
        clip = runtime.DATA_DIR / "sample_bug.mov"
    app_url = f"{str(request.base_url).rstrip('/')}/sampleapp/" if config.SAMPLE_APP.is_dir() else ""
    return {"clip": str(clip) if clip.exists() else "", "app_url": app_url}


@router.post("/webhook")
async def webhook(request: Request) -> dict:
    """GitHub webhook: verify the HMAC signature, then accept (or enqueue) the event."""
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")
    if not verify_signature(forge_auth.webhook_secret(), body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = json.loads(body or b"{}")
    except Exception:
        payload = {}

    video_path = payload.get("video_path", "")
    if video_path:
        setup()
        from taketwo.pipeline.jobs import get_runner

        job_id = get_runner().submit(video_path=video_path, repo=payload.get("repo", ""))
        return {"accepted": True, "job_id": job_id}
    return {"accepted": True, "event": payload.get("action", "unknown")}
