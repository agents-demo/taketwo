"""Ingest: upload a clip, list the demo scenarios, and the GitHub webhook."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from taketwo.core.bootstrap import setup
from taketwo.integrations.forge import auth as forge_auth
from taketwo.integrations.forge import verify_signature
from taketwo.surfaces.gui2.server import config

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


@router.get("/scenarios")
def scenarios(request: Request) -> dict:
    """The bundled demo scenarios: name, title, clip path, and served app URL."""
    base = str(request.base_url).rstrip("/")
    out: list[dict] = []
    root = config.SCENARIOS_DIR
    if root.is_dir():
        for path in sorted(root.iterdir()):
            if not (path / "app" / "index.html").is_file():
                continue
            title = path.name
            try:
                title = json.loads((path / "scenario.json").read_text(encoding="utf-8")).get("title") or path.name
            except Exception:
                pass
            clip = path / "clip.mp4"
            out.append(
                {
                    "name": path.name,
                    "title": title,
                    "clip": str(clip) if clip.exists() else "",
                    "app_url": f"{base}/demoapps/{path.name}/app/",
                    "reproducible": Path(f"{clip}.timeline.json").exists(),
                }
            )
    return {"scenarios": out}


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
        from taketwo.core.jobs import get_runner

        job_id = get_runner().submit(video_path=video_path, repo=payload.get("repo", ""))
        return {"accepted": True, "job_id": job_id}
    return {"accepted": True, "event": payload.get("action", "unknown")}
