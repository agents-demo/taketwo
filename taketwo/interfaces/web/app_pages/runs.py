"""Runs page: submit a recording, watch the job live, browse past runs."""

from __future__ import annotations

import streamlit as st

from taketwo.interfaces.runner import get_runner
from taketwo.interfaces.web import common
from taketwo.interfaces.web.app_pages import detail
from taketwo.storage import runtime


@st.dialog("Run review", width="large", position="right")
def _review_drawer(job: str) -> None:
    detail.render(job)


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


def _new_run() -> None:
    with st.container(border=True):
        st.subheader("New run", icon=":material/rocket_launch:")
        upload = st.file_uploader("Recording — a screen recording or screenshots", type=common.ACCEPTED)
        if upload is not None:
            st.video(upload, alt="Preview of the recording you are about to submit")

        cols = st.columns([1, 1, 1, 1, 1])
        repo = cols[0].text_input("Repository", placeholder="owner/name")
        branch = cols[1].text_input("Base branch", value="main")
        app_url = cols[2].text_input("App URL", placeholder="http://localhost:3000")
        agentic = cols[3].toggle("Agentic")
        submitted = cols[4].button("Record & reproduce", icon=":material/play_arrow:", type="primary")

    if not submitted:
        return
    video_path = common.sample_path()
    if upload is not None:
        target = runtime.DATA_DIR / f"upload_{upload.name}"
        target.write_bytes(upload.getbuffer())
        video_path = str(target)
    if not video_path:
        st.error("Upload a recording, or run `python scripts/make_sample_bug.py` for the sample clip.")
        return
    submission = {"video_path": video_path, "repo": repo, "base_branch": branch, "app_url": app_url, "agentic": agentic}
    job_id = get_runner().submit(**submission)
    st.session_state.update(job_id=job_id, last_submission=submission, refreshed_for=None)
    st.toast(f"Queued run {job_id}", icon=":material/rocket_launch:")


def page() -> None:
    common.init_state()

    st.title("Reproduce a bug from a screen recording", icon=":material/movie:")
    st.caption("Drop the clip a reporter sent, point at the repo; get an issue, a fix, and a before/after video.")

    _new_run()
    live_job()

    st.subheader("Runs", icon=":material/history:")
    verdict = st.segmented_control(
        "Filter runs", list(common.VERDICT_LABELS), default="All", key="verdict", bind="query-params", wrap=True
    )
    data = common.rows(common.VERDICT_LABELS.get(verdict, None))
    if not data:
        with st.container(border=True):
            st.markdown(":material/inbox: **No runs yet**")
            st.caption("Submit a recording above to see the reproduction, fix, and proof.")
        st.stop()

    event = common.runs_dataframe(data)
    jobs = [row["run"] for row in data]

    if event.selection.rows:
        selected = data[event.selection.rows[0]]["run"]
        if st.session_state.get("opened_for") != selected:
            st.session_state["opened_for"] = selected
            _review_drawer(selected)

    job = st.selectbox("Open run", jobs, index=0, key="run", bind="query-params")

    from taketwo.interfaces.web.app_pages import pages

    st.page_link(pages.DETAIL, label=f"Open review for {job}", icon=":material/fact_check:")
