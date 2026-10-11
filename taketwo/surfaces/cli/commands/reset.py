"""``reset`` — clear saved runs."""

from __future__ import annotations

from taketwo.storage import store


def run() -> int:
    store.reset()
    print("Cleared saved runs.")
    return 0
