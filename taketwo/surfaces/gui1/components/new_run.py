"""The "new run" form (upload or pick a demo) and the submit queue."""

from __future__ import annotations

import streamlit as st

from taketwo.core.jobs import get_runner
from taketwo.integrations.storage import runtime
from taketwo.surfaces.gui1 import config, samples


def queue(video_path: str, repo: str, branch: str, app_url: str, agentic: bool) -> None:
    if not video_path:
        st.error("Upload a recording, or pick a demo scenario.")
        return
    submission = {"video_path": video_path, "repo": repo, "base_branch": branch, "app_url": app_url, "agentic": agentic}
    job_id = get_runner().submit(**submission)
    st.session_state.update(job_id=job_id, last_submission=submission, refreshed_for=None)
    st.toast(f"Queued run {job_id}", icon=":material/rocket_launch:")


def new_run() -> None:
    pick = ""
    demo = None
    with st.container(border=True):
        st.subheader("Drop a recording", icon=":material/upload:")
        st.caption("A screen recording or screenshots — shaky is fine.")
        upload = st.file_uploader("Recording", type=config.ACCEPTED, label_visibility="collapsed")
        if upload is not None:
            st.video(upload, alt="Preview of the recording you are about to submit")

        names = samples.scenario_names()
        if names:
            pick = st.selectbox("Demo scenario", names, format_func=samples.scenario_title, key="demo_pick")
            demo = st.button(f"Use the “{samples.scenario_title(pick)}” demo", icon=":material/science:")

        cols = st.columns([1, 1, 1, 1, 1])
        repo = cols[0].text_input("Repository", placeholder="owner/name")
        branch = cols[1].text_input("Base branch", value="main")
        app_url = cols[2].text_input("App URL", placeholder="http://localhost:3000")
        agentic = cols[3].toggle("Agentic")
        submitted = cols[4].button("Record & reproduce", icon=":material/play_arrow:", type="primary")

        st.caption("Typically ~5–15 model calls · 1–5 min, depending on the clip and the app.")

    if submitted:
        video_path = samples.scenario_clip(pick) if pick else ""
        if upload is not None:
            target = runtime.DATA_DIR / f"upload_{upload.name}"
            target.write_bytes(upload.getbuffer())
            video_path = str(target)
        queue(video_path, repo, branch, app_url, agentic)
    elif demo:
        # Demo with no setup: serve the chosen scenario's app and submit its clip.
        queue(samples.scenario_clip(pick), repo, branch, app_url or samples.serve_scenario(pick), agentic)
