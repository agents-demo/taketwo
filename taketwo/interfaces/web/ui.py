"""Streamlit review surface: submit a recording, track the sandboxed job, review the proof.

    streamlit run taketwo/interfaces/web/ui.py
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from taketwo.bootstrap import setup
from taketwo.domain import evaluate, render
from taketwo.interfaces.runner import get_runner
from taketwo.storage import store

setup()

st.set_page_config(page_title="TakeTwo", layout="wide")
st.title("TakeTwo")
st.caption("A screen recording in; a reproduction, a fix, and a before/after proof out.")

with st.sidebar:
    st.header("New run")
    video = st.text_input("Recording path", "runtime/data/sample_bug.mov")
    repo = st.text_input("Repository (owner/name)", "")
    branch = st.text_input("Base branch", "main")
    app_url = st.text_input("App URL", "")
    agentic = st.checkbox("Agentic mode", value=False)
    run = st.button("Record & reproduce", type="primary")


def _progress(path: str) -> dict:
    file = Path(path)
    if not file.exists():
        return {}
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except Exception:
        return {}


if run:
    job_id = get_runner().submit(
        video_path=video, repo=repo, base_branch=branch, app_url=app_url, agentic=agentic
    )
    st.session_state["job_id"] = job_id
    st.session_state["progress_path"] = get_runner().status(job_id).get("progress_path", "")
    st.success(f"Queued job {job_id}")

if job_id := st.session_state.get("job_id"):
    status = get_runner().status(job_id)
    progress = _progress(st.session_state.get("progress_path", ""))
    st.info(
        f"Job {job_id}: {status.get('status')} · "
        f"{progress.get('stage', '')} {progress.get('pct', '')}%"
    )
    if st.button("Check status"):
        st.rerun()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Runs")
    jobs = store.jobs()
    selected = st.radio("Select a run", jobs, label_visibility="collapsed") if jobs else None

with col_right:
    if selected:
        repro = store.get_repro(selected)
        fix = store.get_fix(selected)
        proof = store.get_proof(selected)
        st.subheader("Reproduction")
        st.json(evaluate.score(repro))
        st.markdown(render.issue_markdown({"repo": selected}, repro))
        if fix.get("diff"):
            st.subheader("Fix")
            st.code(fix["diff"], language="diff")
        if proof.get("proof_video") and Path(proof["proof_video"]).exists():
            st.subheader("Proof (before | after)")
            st.video(proof["proof_video"])
        elif proof.get("proof_path") and Path(proof["proof_path"]).exists():
            st.subheader("Proof (before | after)")
            st.image(proof["proof_path"])
    else:
        st.info("No runs yet. Submit a recording from the sidebar.")
