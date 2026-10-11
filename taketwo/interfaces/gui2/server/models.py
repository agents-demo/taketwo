"""Request models for the gui2 server."""

from __future__ import annotations

from pydantic import BaseModel


class ReplayRequest(BaseModel):
    video_path: str
    repo: str = ""
    base_branch: str = "main"
    app_url: str = ""
    agentic: bool = False
