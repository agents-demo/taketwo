"""Runs page: submit a recording, watch the job live, browse past runs."""

from __future__ import annotations

import streamlit as st

from taketwo.pipeline.jobs import get_runner
from taketwo.surfaces.gui1 import config, data, session
from taketwo.surfaces.gui1.app_pages import detail, pages
from taketwo.surfaces.gui1.components import empty_state, live_job, new_run, readiness, runs_table


@st.dialog("Run review", width="large", position="right")
def _review_drawer(job: str) -> None:
    detail.render(job)


def _stats(all_rows: list[dict]) -> None:
    total = len(all_rows)
    reproduced = sum(1 for r in all_rows if r["verdict"] == "reproduced")
    verified = sum(1 for r in all_rows if r["verified"])
    approved = sum(1 for r in all_rows if r["review"] == "approved")
    cols = st.columns(4)
    cols[0].metric("Runs", total)
    cols[1].metric("Reproduced", f"{reproduced}")
    cols[2].metric("Verified", f"{verified}")
    cols[3].metric("Approved", f"{approved}")


def _latest_run(all_rows: list[dict]) -> None:
    """A summary card for the newest run, with a jump to its full review."""
    if not all_rows:
        return
    row = all_rows[0]
    job = row["run"]

    with st.container(border=True):
        st.subheader("Latest run", icon=":material/bolt:")
        st.caption(f"`{job}` · {row['when']}")
        badges = st.container(horizontal=True)
        badges.badge(row["verdict"].replace("_", " "), color="green" if row["verdict"] == "reproduced" else "gray")
        badges.badge("verified" if row["verified"] else "unverified", color="green" if row["verified"] else "gray")
        badges.badge("grounded" if row["grounded"] else "ungrounded", color="blue" if row["grounded"] else "gray")
        metrics = st.columns(3)
        metrics[0].metric("Score", f"{row['score']:.2f}")
        metrics[1].metric("Review", row["review"])
        metrics[2].metric("Verdict", row["verdict"])
        st.page_link(pages.DETAIL, label="Open the full review", icon=":material/fact_check:")


def page() -> None:
    session.init_state()

    st.title("Reproduce a bug from a screen recording", icon=":material/movie:")
    st.caption(config.TAGLINE)

    all_rows = data.rows(None)
    _latest_run(all_rows)

    readiness.strip()
    new_run.new_run()
    live_job.live_job()
    active = get_runner().active()
    if active:
        st.caption(f"{len(active)} run(s) in flight")

    st.space("medium")
    st.subheader("Runs", icon=":material/history:")

    if not all_rows:
        empty_state.empty_state(
            ":material/inbox:", "No runs yet", "Submit a recording above to see the reproduction, fix, and proof."
        )
        st.stop()

    _stats(all_rows)

    verdict = st.segmented_control(
        "Filter runs", list(config.VERDICT_LABELS), default="All", key="verdict", bind="query-params", wrap=True
    )
    label = config.VERDICT_LABELS.get(verdict, None)
    rows = [row for row in all_rows if not label or row["verdict"] == label]

    event = runs_table.runs_dataframe(rows)
    jobs = [row["run"] for row in rows]

    if event.selection.rows:
        selected = rows[event.selection.rows[0]]["run"]
        if st.session_state.get("opened_for") != selected:
            st.session_state["opened_for"] = selected
            _review_drawer(selected)

    job = st.selectbox("Open run", jobs, index=0, key="run", bind="query-params")

    st.page_link(pages.DETAIL, label=f"Open review for {job}", icon=":material/fact_check:")

    st.space("medium")
    st.caption("Open source · free for open-source maintainers · built on openjiuwen")
