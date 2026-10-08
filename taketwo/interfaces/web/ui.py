"""Streamlit review surface: submit a recording, watch progress, review the proof.

    streamlit run taketwo/interfaces/web/ui.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st

from taketwo.bootstrap import setup
from taketwo.domain import evaluate, render
from taketwo.storage import store

setup()

st.set_page_config(page_title="taketwo", layout="wide")
st.title("taketwo")
st.caption("A screen recording in; a reproduction, a fix, and a before/after proof out.")

with st.sidebar:
    st.header("New run")
    video = st.text_input("Recording path", "runtime/data/sample_bug.mp4")
    repo = st.text_input("Repository (owner/name)", "")
    branch = st.text_input("Base branch", "main")
    app_url = st.text_input("App URL", "")
    agentic = st.checkbox("Agentic mode", value=False)
    run = st.button("Record & reproduce", type="primary")


def _run_in_worker() -> None:
    progress_file = Path(tempfile.gettempdir()) / "taketwo_progress.json"
    args = [
        sys.executable,
        "-m",
        "taketwo.interfaces.worker",
        video,
        "--progress",
        str(progress_file),
        "--repo",
        repo,
        "--branch",
        branch,
        "--app",
        app_url,
    ]
    if agentic:
        args.append("--agentic")
    subprocess.run(args, check=False)


if run:
    placeholder = st.empty()
    placeholder.info("Running… (progress streams from the worker process)")
    _run_in_worker()
    placeholder.success("Done.")

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
        if proof.get("proof_path"):
            st.subheader("Proof")
            path = Path(proof["proof_path"])
            if path.exists():
                st.image(str(path))
    else:
        st.info("No runs yet. Submit a recording from the sidebar.")

if (Path(tempfile.gettempdir()) / "taketwo_progress.json").exists():
    with st.expander("Worker progress"):
        st.json(json.loads((Path(tempfile.gettempdir()) / "taketwo_progress.json").read_text(encoding="utf-8")))
