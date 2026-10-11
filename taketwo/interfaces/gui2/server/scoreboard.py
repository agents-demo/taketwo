"""Scoreboard aggregation over the run read model."""

from __future__ import annotations

from typing import Any

from taketwo.interfaces.gui2.server.runs import list_runs


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
