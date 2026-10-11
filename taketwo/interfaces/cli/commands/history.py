"""``history`` — list recent runs."""

from __future__ import annotations

from taketwo.storage import store


def run() -> int:
    found = store.jobs()
    if not found:
        print("No runs yet. Run `record`.")
        return 0
    print(f"Runs ({len(found)}):\n")
    for job in found[:10]:
        repro = store.get_repro(job)
        print(f"  {job} · {repro.get('verdict', '?')} · {repro.get('evidence', {}).get('summary', '')}")
    return 0
