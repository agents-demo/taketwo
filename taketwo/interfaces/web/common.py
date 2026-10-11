"""Shared helpers for the TakeTwo web UI (state, run rows, identity, timeline)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from taketwo.domain import evaluate
from taketwo.interfaces.web.compare import before_after
from taketwo.reporting import proof_card, share_card
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


def reproduce_rate(rows: list[dict]) -> float:
    return (sum(1 for r in rows if r["verdict"] == "reproduced") / len(rows)) if rows else 0.0


# ``share_card`` / ``proof_card`` are re-exported from :mod:`taketwo.reporting` above.


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


def live_sample_path() -> str:
    """The live-sample clip (timeline only, no repro sidecar → reproduces in a browser)."""
    path = runtime.DATA_DIR / "sample_bug_live.mov"
    return str(path) if path.exists() else sample_path()


def sample_app_url(port: int = 8130) -> str:
    """Serve ``examples/sample_app`` locally once and return its URL (for the live demo)."""
    cached = st.session_state.get("_sample_app")
    if cached is not None:
        return getattr(cached, "url", "")
    sample = _ROOT / "examples" / "sample_app"
    if not sample.exists():
        return ""
    import sys

    from taketwo.pipeline import appserver

    command = f'"{sys.executable}" -m http.server {port} --directory "{sample}"'
    app = appserver.start(command, _ROOT, f"http://localhost:{port}")
    if app is not None:
        st.session_state["_sample_app"] = app
        return app.url
    return ""


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
        repo = (summary(job).get("submission") or {}).get("repo") or "local"
        out.append(
            {
                "run": job,
                "repo": repo,
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
            "repo": st.column_config.TextColumn("Repo"),
            "when": st.column_config.TextColumn("When"),
            "verdict": st.column_config.TextColumn("Verdict"),
            "score": st.column_config.ProgressColumn("Score", min_value=0.0, max_value=1.0, format="%.2f"),
            "grounded": st.column_config.CheckboxColumn("Grounded"),
            "verified": st.column_config.CheckboxColumn("Verified"),
            "review": st.column_config.TextColumn("Review"),
        },
        alt="Reproduction runs with verdict, score, and review status",
    )


def rate_trend(rows: list[dict]) -> Any:
    """A line of the cumulative reproduce rate over runs (oldest → newest), or ``None``."""
    if not rows:
        return None
    try:
        import altair as alt
        import pandas as pd

        seen, data = 0, []
        for index, row in enumerate(reversed(rows), start=1):
            seen += int(row["verdict"] == "reproduced")
            data.append({"run": index, "rate": seen / index})
        frame = pd.DataFrame(data)
        return (
            alt.Chart(frame)
            .mark_line(point=True, color="#7C3AED")
            .encode(
                x=alt.X("run:Q", title="run #"),
                y=alt.Y("rate:Q", title="cumulative reproduce rate", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
                tooltip=["run", "rate"],
            )
            .properties(height=220)
        )
    except Exception:
        return None


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
