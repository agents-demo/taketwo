"""A friendly empty-state card."""

from __future__ import annotations

import streamlit as st

from taketwo.surfaces.gui1 import config


def empty_state(icon: str, title: str, body: str) -> None:
    with st.container(border=True):
        if config.EMPTY_ART.exists():
            cols = st.columns([1, 2, 1])
            cols[1].image(str(config.EMPTY_ART), width="stretch")
        st.markdown(f"### {icon} {title}")
        st.caption(body)
