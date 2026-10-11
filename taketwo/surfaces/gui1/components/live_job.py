"""The live job feed: progress bar, per-stage steps, cancel / retry."""

from __future__ import annotations

import streamlit as st

from taketwo.core.jobs import get_runner


@st.fragment(run_every=2.0)
def live_job() -> None:
    job_id = st.session_state.get("job_id")
    if not job_id:
        return

    status = get_runner().status(job_id)
    state = status.get("status", "unknown")
    progress = status.get("progress") or {}
    pct = float(progress.get("pct") or 0) / 100
    colour = {"done": "green", "failed": "red", "running": "blue", "cancelled": "orange"}.get(state, "gray")

    with st.container(border=True):
        head = st.columns([5, 1, 1])
        head[0].markdown(f"**Run `{job_id}`** — {progress.get('stage', 'starting')}")
        head[1].badge(state.capitalize(), color=colour)
        if state in ("queued", "running") and head[2].button("Cancel", icon=":material/stop_circle:"):
            get_runner().cancel(job_id)
            st.rerun()
        st.progress(min(1.0, max(0.0, pct)), text=f"{progress.get('stage', 'starting')} · {int(pct * 100)}%")

        for step in progress.get("timings") or []:
            st.status(step.get("stage", "stage"), state="complete", type="step")
        current = progress.get("stage", "starting")
        if state in ("queued", "running"):
            st.status(current, state="running", type="step", expanded=False)
        elif state == "failed":
            st.status(current, state="error", type="step")
        elif state == "done":
            st.status(current, state="complete", type="step")

        if state == "failed":
            st.error(status.get("error") or "worker failed")
            if st.button("Retry", icon=":material/refresh:", key="retry_failed"):
                get_runner().submit(**st.session_state["last_submission"])
                st.rerun()
        if state in ("done", "cancelled") and st.session_state.get("refreshed_for") != job_id:
            st.session_state["refreshed_for"] = job_id
            st.rerun()
