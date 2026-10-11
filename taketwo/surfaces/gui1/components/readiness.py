"""The readiness strip: what is configured before a run (model / browser / delivery / sample)."""

from __future__ import annotations

import streamlit as st

from taketwo import readiness


def strip() -> None:
    items = readiness.checks()
    with st.container(border=True):
        st.caption("Readiness")
        st.markdown("  ·  ".join(f"{'✅' if c['ok'] else '⚠️'} {c['name']}" for c in items))
        for c in items:
            if not c["ok"]:
                st.caption(f"⚠️ {c['name']}: {c['detail']}")
