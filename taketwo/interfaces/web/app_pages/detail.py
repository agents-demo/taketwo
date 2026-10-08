"""Run detail: proof (video + comparison), fix, evidence, review workflow, and a follow-up chat."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from taketwo.domain import evaluate
from taketwo.interfaces import service
from taketwo.interfaces.web import common
from taketwo.interfaces.web.compare import before_after
from taketwo.storage import store


def _chat(job: str) -> None:
    history = st.session_state.setdefault(f"chat_{job}", [])
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("Ask about this run…")
    if not prompt:
        return
    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    answer = service.ask_sync(job, prompt)
    history.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)


def render(job: str) -> None:
    """Render the full review surface for one run."""
    repro = store.get_repro(job)
    fix = store.get_fix(job)
    proof = store.get_proof(job)
    review = store.get_review(job)
    summary = common.summary(job)
    delivery = summary.get("delivery") or {}
    usage = summary.get("usage") or {}
    submission = summary.get("submission") or {}
    score = evaluate.score(repro)
    verification = proof.get("verification") or {}
    verdict = repro.get("verdict", "unclear")

    with st.container(border=True):
        head = st.columns([5, 1])
        head[0].markdown(f"#### `{job}` :{verdict}-badge[{verdict}]")
        head[1].badge(review.get("status", "pending").replace("_", " ").title(), color="gray")

        context = " · ".join(
            part
            for part in (
                f":material/schedule: {common.when(job)}",
                f":material/account_tree: {submission.get('base_branch', 'main')}",
                f":material/movie: {Path(submission.get('video_path', '')).name}"
                if submission.get("video_path")
                else "",
            )
            if part
        )
        if context:
            st.caption(context)
        if repro.get("evidence", {}).get("summary"):
            st.caption(f"Evidence: {repro['evidence']['summary']}")

        metrics = st.columns(5)
        metrics[0].metric("Score", f"{score['score']:.2f}")
        metrics[1].metric("Grounded", "yes" if score["grounded"] else "no")
        metrics[2].metric("Verified", "yes" if verification.get("verified") else "no")
        metrics[3].metric("Steps", len(repro.get("steps", [])))
        metrics[4].metric("Tokens", f"{int(usage.get('total_tokens', 0)):,}")

    proof_tab, fix_tab, evidence_tab, review_tab = st.tabs(
        [":material/movie: Proof", ":material/code: Fix", ":material/rule: Evidence", ":material/fact_check: Review"]
    )

    with proof_tab:
        video = proof.get("proof_video")
        before, after = repro.get("before_clip", ""), proof.get("after_clip", "")
        if video and Path(video).exists():
            st.caption("The same scenario, before and after the fix.")
            st.video(video, alt="Proof video: the same scenario before and after the fix")
        if before and after and Path(before).exists() and Path(after).exists():
            with st.expander("Compare stills (drag to reveal)", icon=":material/compare:"):
                before_after(before, after, key=f"cmp_{job}")
        elif not (video and Path(video).exists()):
            st.caption("No proof yet — the re-run needs a live browser or the sandbox.")

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
        chart = common.activity_chart(summary.get("timings"))
        if chart is not None:
            st.markdown("**Pipeline timeline**")
            st.altair_chart(chart, width="stretch")
        tools = common.read_json(summary.get("artifacts", {}).get("observability", "")).get("tools", [])
        if tools:
            st.markdown("**Model & tool activity**")
            st.dataframe(
                [{"tool": t.get("name"), "seconds": t.get("seconds"), "arguments": t.get("arguments")} for t in tools],
                hide_index=True,
                width="stretch",
                alt="Tool calls made during the run",
            )
        console = repro.get("evidence", {}).get("console") or []
        if console:
            st.code("\n".join(console), language="text")
        if repro.get("question"):
            st.info(repro["question"], icon=":material/help:")

    with review_tab:
        st.caption(f"Reviewing as {common.actor()}")
        note = st.text_input("Note", placeholder="Why approve or send back…", label_visibility="collapsed")
        actions = st.container(horizontal=True)
        approve = actions.button(
            "Approve & merge", type="primary", icon=":material/check_circle:", disabled=not verification.get("verified")
        )
        changes = actions.button("Request changes", icon=":material/undo:")
        if approve:
            store.set_review(job, "approved", note, actor=common.actor())
            st.toast(f"Approved {job}", icon=":material/check_circle:")
            st.rerun()
        if changes:
            store.set_review(job, "changes_requested", note, actor=common.actor())
            st.toast(f"Sent {job} back for changes", icon=":material/undo:")
            st.rerun()
        if not verification.get("verified"):
            st.caption("Approve is disabled until the fix is verified (a browser re-run or tests actually ran).")

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
        _chat(job)


def page() -> None:
    common.init_state()
    st.title("Run review", icon=":material/fact_check:")
    jobs = store.jobs()
    if not jobs:
        st.info("No runs yet — submit one on the Runs page.", icon=":material/inbox:")
        return
    job = st.selectbox("Run", jobs, index=0, key="run", bind="query-params")
    render(job)
