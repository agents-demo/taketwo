"""The page registry (single source of truth for ``st.navigation`` and page links)."""

from __future__ import annotations

import streamlit as st

from taketwo.interfaces.web.app_pages import detail, runs

RUNS = st.Page(runs.page, title="Runs", icon=":material/history:", url_path="runs", default=True)
DETAIL = st.Page(detail.page, title="Run review", icon=":material/fact_check:", url_path="run")


def navigation() -> None:
    st.navigation([RUNS, DETAIL]).run()
