"""Runs, scoreboard, ask, and review."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from taketwo.bootstrap import setup
from taketwo.surfaces.gui2.server import runs as read_model
from taketwo.surfaces.gui2.server.scoreboard import scoreboard as build_scoreboard

router = APIRouter()


@router.get("/runs")
def runs() -> dict:
    return {"runs": read_model.list_runs()}


@router.get("/runs/{job}")
def run(job: str) -> dict:
    found = read_model.get_run(job)
    if found is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return found


@router.get("/scoreboard")
def scoreboard() -> dict:
    return build_scoreboard()


@router.get("/runs/{job}/ask")
def ask(job: str, q: str) -> dict:
    from taketwo.core import service

    if not q.strip():
        raise HTTPException(status_code=400, detail="empty question")
    if read_model.get_run(job) is None:
        raise HTTPException(status_code=404, detail="unknown run")
    setup()
    return {"answer": service.ask_sync(job, q)}


@router.post("/runs/{job}/review/{decision}")
def review(job: str, decision: str, note: str = "", actor: str = "web") -> dict:
    from taketwo.integrations.storage import store

    if decision not in ("approved", "changes_requested", "pending"):
        raise HTTPException(status_code=400, detail="invalid decision")
    if read_model.get_run(job) is None:
        raise HTTPException(status_code=404, detail="unknown run")
    store.set_review(job, decision, note, actor=actor or "web")
    return store.get_review(job)
