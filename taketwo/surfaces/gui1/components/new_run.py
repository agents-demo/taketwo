"""The "new run" form: run a bundled demo, or your own bug (upload + repo/app)."""

from __future__ import annotations

import streamlit as st

from taketwo.core.jobs import get_runner
from taketwo.integrations.storage import runtime
from taketwo.surfaces.gui1 import config, samples


def queue(video_path: str, repo: str, branch: str, app_url: str, agentic: bool) -> None:
    if not video_path:
        st.error("Upload a recording, or paste a clip path.")
        return
    submission = {"video_path": video_path, "repo": repo, "base_branch": branch, "app_url": app_url, "agentic": agentic}
    job_id = get_runner().submit(**submission)
    st.session_state.update(job_id=job_id, last_submission=submission, refreshed_for=None)
    st.toast(f"Queued run {job_id}", icon=":material/rocket_launch:")


def _demo_tab() -> None:
    names = samples.scenario_names()
    if not names:
        st.caption("No demos found under demos/scenarios/.")
        return
    pick = st.selectbox("Bundled demo", names, format_func=samples.scenario_label, key="demo_pick")
    if st.button(f"Run the “{samples.scenario_title(pick)}” demo", type="primary", icon=":material/play_arrow:"):
        queue(samples.scenario_clip(pick), "", "main", samples.serve_scenario(pick), False)
    st.caption("✅ = has a fallback timeline · the model still reads the recording.")


def _own_tab() -> None:
    clip_path = st.text_input("Clip path", placeholder="or upload a recording below")
    upload = st.file_uploader("Recording", type=config.ACCEPTED, label_visibility="collapsed")
    if upload is not None:
        st.video(upload, alt="Preview of the recording you are about to submit")

    cols = st.columns([1, 1, 1, 1, 1])
    repo = cols[0].text_input("Repository", placeholder="owner/name (optional)")
    branch = cols[1].text_input("Base branch", value="main")
    app_url = cols[2].text_input("App URL", placeholder="http://localhost:3000")
    agentic = cols[3].toggle("Agentic")
    submitted = cols[4].button("Record & reproduce", icon=":material/play_arrow:", type="primary")
    st.caption("A repository is only needed for the fix + proof.")

    if submitted:
        video_path = clip_path.strip()
        if upload is not None:
            target = runtime.DATA_DIR / f"upload_{upload.name}"
            target.write_bytes(upload.getbuffer())
            video_path = str(target)
        queue(video_path, repo, branch, app_url, agentic)


def new_run() -> None:
    with st.container(border=True):
        st.subheader("New run", icon=":material/play_arrow:")
        st.caption("Reproduce a bug from a recording — start from a demo, or use your own bug.")
        demo_tab, own_tab = st.tabs(["Try a demo", "Your own bug"])
        with demo_tab:
            _demo_tab()
        with own_tab:
            _own_tab()
        st.caption("Typically ~5–15 model calls · 1–5 min.")
