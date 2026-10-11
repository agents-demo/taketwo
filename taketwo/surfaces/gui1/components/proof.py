"""The full-width before/after proof hero (video, else drag-compare)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from taketwo.surfaces.gui1.components.compare import before_after


def proof_hero(repro: dict, proof: dict, job: str) -> bool:
    """Render the before/after proof full width (video hero, else slider). True if shown."""
    video = proof.get("proof_video")
    before, after = repro.get("before_clip", ""), proof.get("after_clip", "")
    if video and Path(video).exists():
        st.video(video, alt="The same scenario before and after the fix")
        return True
    if before and after and Path(before).exists() and Path(after).exists():
        before_after(before, after, key=f"hero_{job}")
        return True
    return False
