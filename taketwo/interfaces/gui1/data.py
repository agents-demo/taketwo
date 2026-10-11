"""Read model for gui1: run rows and per-run summaries from the store."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from taketwo.domain import evaluate
from taketwo.storage import runtime, store


def read_json(path: str | Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def summary(job: str) -> dict:
    return read_json(runtime.ARTIFACTS_DIR / f"{job}_summary.json")


def when(job: str) -> str:
    try:
        ts = (runtime.DATA_DIR / f"{job}_repro.json").stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def rows(verdict_filter: str | None) -> list[dict[str, Any]]:
    """One row per run, newest first, honouring the verdict filter."""
    out: list[dict[str, Any]] = []
    for job in store.jobs():
        score = evaluate.score(store.get_repro(job))
        if verdict_filter and score["verdict"] != verdict_filter:
            continue
        proof = store.get_proof(job)
        repo = (summary(job).get("submission") or {}).get("repo") or "local"
        out.append(
            {
                "run": job,
                "repo": repo,
                "when": when(job),
                "verdict": score["verdict"],
                "score": float(score["score"]),
                "grounded": bool(score["grounded"]),
                "verified": bool((proof.get("verification") or {}).get("verified")),
                "review": store.get_review(job).get("status", "pending"),
            }
        )
    return out


def reproduce_rate(rows: list[dict]) -> float:
    return (sum(1 for r in rows if r["verdict"] == "reproduced") / len(rows)) if rows else 0.0
