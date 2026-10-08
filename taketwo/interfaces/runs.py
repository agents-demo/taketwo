"""Read model for runs and the scoreboard (no Streamlit), shared by the API and UIs."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from taketwo.domain import evaluate
from taketwo.storage import json_store, runtime, store


def _when(job: str) -> str:
    try:
        stamp = (runtime.DATA_DIR / f"{job}_repro.json").stat().st_mtime
        return datetime.fromtimestamp(stamp, tz=UTC).isoformat(timespec="seconds")
    except Exception:
        return ""


def _summary(job: str) -> dict:
    value = json_store.read_json(runtime.ARTIFACTS_DIR / f"{job}_summary.json", {})
    return value if isinstance(value, dict) else {}


def _exists(path: str) -> bool:
    return bool(path) and Path(path).exists()


def list_runs() -> list[dict[str, Any]]:
    """One dict per run (newest first), with media availability flags."""
    out: list[dict[str, Any]] = []
    for job in store.jobs():
        repro, fix, proof, review = (
            store.get_repro(job),
            store.get_fix(job),
            store.get_proof(job),
            store.get_review(job),
        )
        score = evaluate.score(repro)
        repo = (_summary(job).get("submission") or {}).get("repo") or "local"
        if repo and "/" not in repo:
            repo = "local"
        out.append(
            {
                "job": job,
                "repo": repo if repo != "local" else "local",
                "when": _when(job),
                "verdict": score["verdict"],
                "score": round(float(score["score"]), 3),
                "grounded": bool(score["grounded"]),
                "verified": bool((proof.get("verification") or {}).get("verified")),
                "review": review.get("status", "pending"),
                "evidence": repro.get("evidence", {}).get("summary", ""),
                "question": repro.get("question", ""),
                "steps": repro.get("steps", []),
                "diff": fix.get("diff", ""),
                "test": fix.get("test", ""),
                "has_video": _exists(proof.get("proof_video", "")),
                "has_before": _exists(repro.get("before_clip", "")),
                "has_after": _exists(proof.get("after_clip", "")),
            }
        )
    return out


def get_run(job: str) -> dict[str, Any] | None:
    """One run, including its model/tool observability (usage, calls, tools)."""
    found = next((r for r in list_runs() if r["job"] == job), None)
    if found is None:
        return None
    summary = _summary(job)
    obs = json_store.read_json(runtime.ARTIFACTS_DIR / f"{job}_observability.json", {})
    obs = obs if isinstance(obs, dict) else {}
    found["usage"] = summary.get("usage") or {}
    found["calls"] = obs.get("calls", []) or []
    found["tools"] = obs.get("tools", []) or []
    return found


def scoreboard() -> dict[str, Any]:
    """Aggregate reproduce/verified/approved rates, overall and per repo."""
    rows = list_runs()
    total = len(rows)
    reproduced = sum(1 for r in rows if r["verdict"] == "reproduced")
    verified = sum(1 for r in rows if r["verified"])
    approved = sum(1 for r in rows if r["review"] == "approved")

    repos: dict[str, dict[str, int]] = {}
    for row in rows:
        entry = repos.setdefault(row["repo"], {"runs": 0, "reproduced": 0, "verified": 0})
        entry["runs"] += 1
        entry["reproduced"] += int(row["verdict"] == "reproduced")
        entry["verified"] += int(row["verified"])

    return {
        "total": total,
        "reproduced": reproduced,
        "verified": verified,
        "approved": approved,
        "rate": round(reproduced / total, 3) if total else 0.0,
        "repos": [
            {"repo": name, **counts, "rate": round(counts["reproduced"] / counts["runs"], 3)}
            for name, counts in sorted(repos.items(), key=lambda kv: (kv[1]["reproduced"], kv[1]["runs"]), reverse=True)
        ],
        "feed": rows,
    }
