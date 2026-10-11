"""Run review page: the proof hero, fix, evidence, review workflow, and a chat."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from taketwo.domain import evaluate
from taketwo.integrations.storage import runtime, store
from taketwo.surfaces.gui1 import charts, data, session
from taketwo.surfaces.gui1.components import chat, empty_state, execution, proof, run_summary
from taketwo.surfaces.gui1.components.compare import before_after


def render(job: str) -> None:
    """Render the full review surface for one run."""
    repro = store.get_repro(job)
    fix = store.get_fix(job)
    proof_data = store.get_proof(job)
    review = store.get_review(job)
    summary = data.summary(job)
    delivery = summary.get("delivery") or {}
    score = evaluate.score(repro)
    verification = proof_data.get("verification") or {}

    if not proof.proof_hero(repro, proof_data, job):
        source = next((runtime.ARTIFACTS_DIR / job).glob("source.*"), None)
        if source is not None:
            st.caption("Source recording — no proof yet (this run didn't reproduce).")
            st.video(str(source))

    run_summary.render(job, repro, proof_data, review, summary, score)

    proof_tab, fix_tab, evidence_tab, review_tab = st.tabs(
        [":material/movie: Proof", ":material/code: Fix", ":material/rule: Evidence", ":material/fact_check: Review"]
    )

    with proof_tab:
        before, after = repro.get("before_clip", ""), proof_data.get("after_clip", "")
        if before and after and Path(before).exists() and Path(after).exists():
            st.caption("The same scenario, before and after — drag to compare.")
            before_after(before, after, key=f"cmp_{job}")
        else:
            st.caption("No before/after stills — screenshots need a live browser.")
        video = proof_data.get("proof_video")
        if video and Path(video).exists():
            st.download_button(
                "Download the proof video",
                data=Path(video).read_bytes(),
                file_name=f"{job}_proof.mp4",
                mime="video/mp4",
                icon=":material/download:",
            )

    with fix_tab:
        st.code(fix.get("diff") or "(no diff proposed)", language="diff")
        if fix.get("culprits"):
            st.caption("Suspected cause: " + ", ".join(fix["culprits"][:3]))
        if fix.get("test"):
            st.markdown("**Regression test**")
            st.code(fix["test"], language="python")

    with evidence_tab:
        steps = repro.get("steps", [])
        if steps:
            st.dataframe(
                [
                    {
                        "action": s.get("action"),
                        "target": s.get("target"),
                        "value": s.get("value"),
                        "t (s)": s.get("timestamp"),
                        "confidence": s.get("confidence"),
                    }
                    for s in steps
                ],
                hide_index=True,
                width="stretch",
                alt="Inferred reproduction steps",
            )
        chart = charts.activity_chart(summary.get("timings"))
        if chart is not None:
            st.markdown("**Pipeline timeline**")
            st.altair_chart(chart, width="stretch")
        observability = data.read_json(summary.get("artifacts", {}).get("observability", ""))
        execution.render_execution(observability)
        console = repro.get("evidence", {}).get("console") or []
        if console:
            st.code("\n".join(console), language="text")
        if repro.get("question"):
            st.info(repro["question"], icon=":material/help:")

    with review_tab:
        st.caption(f"Reviewing as {session.actor()}")
        note = st.text_input("Note", placeholder="Why approve or send back…", label_visibility="collapsed")
        actions = st.container(horizontal=True)
        approve = actions.button(
            "Approve", type="primary", icon=":material/check_circle:", disabled=not verification.get("verified")
        )
        changes = actions.button("Request changes", icon=":material/undo:")
        if approve:
            store.set_review(job, "approved", note, actor=session.actor())
            st.toast(f"Approved {job}", icon=":material/check_circle:")
            st.balloons()
            st.rerun()
        if changes:
            store.set_review(job, "changes_requested", note, actor=session.actor())
            st.toast(f"Sent {job} back for changes", icon=":material/undo:")
            st.rerun()
        if not verification.get("verified"):
            st.caption("Approve is disabled until the fix is verified (a browser re-run or tests actually ran).")
        st.caption("Approval is recorded here (with an audit entry); the draft PR is merged by a human on GitHub.")

        pr, issue = delivery.get("pr") or {}, delivery.get("issue") or {}
        links = st.container(horizontal=True)
        if pr.get("url"):
            links.link_button("Open pull request", pr["url"], icon=":material/open_in_new:")
        if issue.get("url"):
            links.link_button("Open issue", issue["url"], icon=":material/open_in_new:")

        audit = review.get("audit") or []
        if audit:
            st.markdown("**Audit trail**")
            st.dataframe(
                [
                    {"action": a.get("action"), "note": a.get("note"), "actor": a.get("actor"), "when": a.get("when")}
                    for a in audit
                ],
                hide_index=True,
                width="stretch",
                alt="Review decisions for this run",
            )
        else:
            st.caption("No decisions yet.")

    with st.container(border=True):
        st.subheader("Ask about this run", icon=":material/forum:")
        chat.chat(job)


def page() -> None:
    session.init_state()
    st.title("Run review", icon=":material/fact_check:")
    jobs = store.jobs()
    if not jobs:
        empty_state.empty_state(":material/inbox:", "No runs yet", "Submit a recording on the Runs page.")
        return
    job = st.selectbox("Run", jobs, index=0, key="run", bind="query-params")
    render(job)
