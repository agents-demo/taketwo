"""``reset`` — clear saved runs."""

from __future__ import annotations

from taketwo.integrations.storage import store


def run() -> int:
    store.reset()
    print("Cleared saved runs.")
    return 0
