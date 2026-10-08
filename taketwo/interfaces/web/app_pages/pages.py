"""The page registry (single source of truth for ``st.navigation`` and page links)."""

from __future__ import annotations

import streamlit as st

from taketwo.interfaces.web.app_pages import detail, runs, scoreboard

RUNS = st.Page(runs.page, title="Runs", icon=":material/history:", url_path="runs", default=True)
DETAIL = st.Page(detail.page, title="Run review", icon=":material/fact_check:", url_path="run")
SCORE = st.Page(scoreboard.page, title="Scoreboard", icon=":material/emoji_events:", url_path="scoreboard")


def navigation() -> None:
    with st.sidebar:
        st.markdown("### TakeTwo")
        st.caption("video in · proof out")
    st.navigation([RUNS, DETAIL, SCORE]).run()
