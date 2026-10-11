"""Share actions: download the proof clip + caption, plus the report cards."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from taketwo.integrations.reporting import proof_card, share_card  # noqa: F401  (re-exported for the pages)
from taketwo.integrations.storage import store


def share(job: str) -> None:
    """One-tap share: download the proof clip + copy a ready-to-post caption."""
    repro, proof = store.get_repro(job), store.get_proof(job)
    verification = proof.get("verification") or {}
    video = proof.get("proof_video")
    if video and Path(video).exists():
        st.download_button(
            "Download the proof clip",
            data=Path(video).read_bytes(),
            file_name=f"{job}_proof.mp4",
            mime="video/mp4",
            icon=":material/download:",
        )
    signal = repro.get("evidence", {}).get("summary") or "reproduced from the clip"
    caption = (
        "TakeTwo turned a screen recording into a fix \U0001f3ac\n"
        f"`{job}` — {repro.get('verdict', 'unclear')} · "
        f"{'verified' if verification.get('verified') else 'unverified'}\n"
        f"{signal}\n\n#TakeTwo #openjiuwen"
    )
    st.caption("Caption — tap the copy icon:")
    st.code(caption, language=None)
