"""Altair charts: cumulative reproduce-rate trend and the pipeline stage timeline."""

from __future__ import annotations

from typing import Any


def rate_trend(rows: list[dict]) -> Any:
    """A line of the cumulative reproduce rate over runs (oldest → newest), or ``None``."""
    if not rows:
        return None
    try:
        import altair as alt
        import pandas as pd

        seen, data = 0, []
        for index, row in enumerate(reversed(rows), start=1):
            seen += int(row["verdict"] == "reproduced")
            data.append({"run": index, "rate": seen / index})
        frame = pd.DataFrame(data)
        return (
            alt.Chart(frame)
            .mark_line(point=True, color="#7C3AED")
            .encode(
                x=alt.X("run:Q", title="run #"),
                y=alt.Y("rate:Q", title="cumulative reproduce rate", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
                tooltip=["run", "rate"],
            )
            .properties(height=220)
        )
    except Exception:
        return None


def activity_chart(timings: list[dict]) -> Any:
    """A horizontal timeline of pipeline stages (``[{stage, seconds}]``) or ``None``."""
    items = [t for t in (timings or []) if t.get("stage")]
    if not items:
        return None
    try:
        import altair as alt
        import pandas as pd

        rows_, cursor = [], 0.0
        for item in items:
            seconds = float(item.get("seconds") or 0)
            rows_.append({"stage": item["stage"], "start": cursor, "end": cursor + seconds})
            cursor += seconds
        frame = pd.DataFrame(rows_)
        return (
            alt.Chart(frame)
            .mark_bar(cornerRadius=3)
            .encode(
                x=alt.X("start:Q", title="seconds"),
                x2="end:Q",
                y=alt.Y("stage:N", sort=None, title=None),
                color=alt.value("#3B82F6"),
                tooltip=["stage", "start", "end"],
            )
            .properties(height=max(60, 26 * len(rows_)))
        )
    except Exception:
        return None
