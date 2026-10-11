"""``show`` — print a run's issue text."""

from __future__ import annotations

from taketwo.domain import render
from taketwo.storage import store


def run(job: str | None) -> int:
    selected = job or store.latest()
    if not selected:
        print("No runs yet.")
        return 0
    repro = store.get_repro(selected) or {}
    print(render.issue_markdown({"repo": selected}, repro))
    return 0
