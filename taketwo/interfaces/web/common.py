"""Shared helpers for the TakeTwo web UI (state, run rows, identity, timeline)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from taketwo.domain import evaluate
from taketwo.interfaces.web.compare import before_after
from taketwo.storage import runtime, store

_ROOT = Path(__file__).resolve().parents[3]
LOGO = _ROOT / "assets" / "taketwo.svg"
EMPTY_ART = _ROOT / "assets" / "empty.svg"
TAGLINE = "A screen recording in. A reproduction, a fix, and before/after proof out."

ACCEPTED = ["mp4", "mov", "webm", "mkv", "png", "jpg", "jpeg", "webp"]
VERDICT_LABELS = {"All": None, "Reproduced": "reproduced", "Not reproduced": "not_reproduced", "Unclear": "unclear"}


def empty_state(icon: str, title: str, body: str) -> None:
    with st.container(border=True):
        if EMPTY_ART.exists():
            cols = st.columns([1, 2, 1])
            cols[1].image(str(EMPTY_ART), width="stretch")
        st.markdown(f"### {icon} {title}")
        st.caption(body)


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


def init_state() -> None:
    st.session_state.setdefault("job_id", None)
    st.session_state.setdefault("refreshed_for", None)
    st.session_state.setdefault("last_submission", None)
    st.session_state.setdefault("opened_for", None)


def sample_path() -> str:
    path = runtime.DATA_DIR / "sample_bug.mov"
    return str(path) if path.exists() else ""


def read_json(path: str | Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def summary(job: str) -> dict:
    return read_json(runtime.ARTIFACTS_DIR / f"{job}_summary.json")


def when(job: str) -> str:
    try:
        ts = (runtime.DATA_DIR / f"{job}_repro.json").stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def actor() -> str:
    """Who is reviewing — from OIDC (``st.user``) when signed in, else the local operator."""
    user = getattr(st, "user", None)
    for attr in ("email", "name"):
        value = getattr(user, attr, None)
        if value:
            return str(value)
    return "maintainer (local)"


def rows(verdict_filter: str | None) -> list[dict[str, Any]]:
    """One row per run, newest first, honouring the verdict filter."""
    out: list[dict[str, Any]] = []
    for job in store.jobs():
        score = evaluate.score(store.get_repro(job))
        if verdict_filter and score["verdict"] != verdict_filter:
            continue
        proof = store.get_proof(job)
        out.append(
            {
                "run": job,
                "when": when(job),
                "verdict": score["verdict"],
                "score": float(score["score"]),
                "grounded": bool(score["grounded"]),
                "verified": bool((proof.get("verification") or {}).get("verified")),
                "review": store.get_review(job).get("status", "pending"),
            }
        )
    return out


def runs_dataframe(data: list[dict]):
    """The runs table; returns the selection event (single-row)."""
    return st.dataframe(
        data,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "run": st.column_config.TextColumn("Run", width="large"),
            "when": st.column_config.TextColumn("When"),
            "verdict": st.column_config.TextColumn("Verdict"),
            "score": st.column_config.ProgressColumn("Score", min_value=0.0, max_value=1.0, format="%.2f"),
            "grounded": st.column_config.CheckboxColumn("Grounded"),
            "verified": st.column_config.CheckboxColumn("Verified"),
            "review": st.column_config.TextColumn("Review"),
        },
        alt="Reproduction runs with verdict, score, and review status",
    )


def activity_chart(timings: list[dict]) -> Any:
    """A horizontal timeline of pipeline stages (``[{stage, seconds}]``) or ``None``."""
    items = [t for t in (timings or []) if t.get("stage")]
    if not items:
        return None
    try:
        import altair as alt
        import pandas as pd

        rows_, cursor = [], 0.0
        for item in items:
            seconds = float(item.get("seconds") or 0)
            rows_.append({"stage": item["stage"], "start": cursor, "end": cursor + seconds})
            cursor += seconds
        frame = pd.DataFrame(rows_)
        return (
            alt.Chart(frame)
            .mark_bar(cornerRadius=3)
            .encode(
                x=alt.X("start:Q", title="seconds"),
                x2="end:Q",
                y=alt.Y("stage:N", sort=None, title=None),
                color=alt.value("#3B82F6"),
                tooltip=["stage", "start", "end"],
            )
            .properties(height=max(60, 26 * len(rows_)))
        )
    except Exception:
        return None
