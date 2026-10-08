"""Pure before/after comparison of two reproduction runs."""

from __future__ import annotations

from typing import Any


def before_after(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Describe what changed between the before and after runs."""
    was = before.get("verdict", "unclear")
    now = after.get("verdict", "unclear")
    fixed = was == "reproduced" and now == "not_reproduced"
    if fixed:
        text = "Reproduced before the fix; the scenario passes after it."
    elif was == now:
        text = f"No change in the scenario (still {now})."
    else:
        text = f"Scenario changed from {was} to {now}."
    return {
        "fixed": fixed,
        "before": was,
        "after": now,
        "text": text,
    }
