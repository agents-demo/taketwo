"""The runs table widget (single-row selectable)."""

from __future__ import annotations

import streamlit as st


def runs_dataframe(data: list[dict]):
    """The runs table; returns the selection event (single-row)."""
    return st.dataframe(
        data,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "run": st.column_config.TextColumn("Run", width="large"),
            "repo": st.column_config.TextColumn("Repo"),
            "when": st.column_config.TextColumn("When"),
            "verdict": st.column_config.TextColumn("Verdict"),
            "score": st.column_config.ProgressColumn("Score", min_value=0.0, max_value=1.0, format="%.2f"),
            "grounded": st.column_config.CheckboxColumn("Grounded"),
            "verified": st.column_config.CheckboxColumn("Verified"),
            "review": st.column_config.TextColumn("Review"),
        },
        alt="Reproduction runs with verdict, score, and review status",
    )
