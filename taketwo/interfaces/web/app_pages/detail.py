"""Run detail: the proof hero, the fix, the evidence, the review workflow, and a chat."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from taketwo.domain import evaluate
from taketwo.interfaces import service
from taketwo.interfaces.web import common
from taketwo.interfaces.web.compare import before_after
from taketwo.storage import runtime, store


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


def _render_execution(observability: dict) -> None:
    """The execution timeline: model + tool calls in order, with I/O and latency."""
    events: list[tuple[str, Any, dict]] = []
    for call in observability.get("calls", []):
        events.append(("model", call.get("seq", 0), call))
    for tool in observability.get("tools", []):
        events.append(("tool", tool.get("seq", 1000), tool))
    if not events:
        return
    events.sort(key=lambda event: event[1] or 0)

    st.markdown("**Execution**")
    st.caption("Ordered by when each model/tool call started.")
    for kind, _seq, event in events:
        seconds = event.get("seconds")
        if kind == "tool":
            title = f"Tool · {event.get('name', '')}" + (f" · {seconds}s" if seconds is not None else "")
            with st.expander(title):
                st.markdown("**Input — arguments passed to the tool**")
                st.code(str(event.get("arguments") or "{}"), language="json")
                if event.get("error"):
                    st.error(str(event["error"]))
                st.markdown("**Output — result the tool returned**")
                st.code(str(event.get("result", "")), language="text")
            continue

        requested = event.get("requested") or []
        prompt, completion = event.get("prompt_tokens"), event.get("completion_tokens")
        title = f"↳ Model call · {event.get('model') or ''}"
        if prompt is not None:
            title += f" · {prompt} in / {completion or 0} out"
        if requested:
            title += "  →  calls " + ", ".join(str(c.get("name", "")) for c in requested)
        if seconds is not None:
            title += f" · {seconds}s"
        with st.expander(title):
            offered = event.get("tools") or []
            if offered:
                st.caption("Tools offered to the model: " + ", ".join(offered))
            st.markdown("**Input — everything sent to the model**")
            messages = event.get("input") or []
            if not messages:
                st.caption("Input not saved (SAVE_CALL_IO is off) or unavailable.")
            for message in messages:
                role = message.get("role", "")
                content = message.get("content", "")
                if role == "assistant" and not str(content).strip():
                    content = "(no text — the model called a tool here)"
                st.markdown(f"*{role}*")
                st.code(content, language="text")
            st.markdown("**Output — what the model produced**")
            for call in requested:
                st.markdown(f"↳ requested tool `{call.get('name', '')}` with:")
                st.code(str(call.get("arguments") or "{}"), language="json")
            if event.get("output"):
                st.code(event["output"], language="text")
            elif requested:
                st.caption("No text — the model only requested tool calls on this turn.")


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

    if not common.proof_hero(repro, proof, job):
        source = next((runtime.ARTIFACTS_DIR / job).glob("source.*"), None)
        if source is not None:
            st.caption("Source recording — no proof yet (this run didn't reproduce).")
            st.video(str(source))

    with st.container(border=True):
        head = st.columns([5, 1])
        head[0].markdown(f"### `{job}`")
        head[1].badge(review.get("status", "pending").replace("_", " ").title(), color="gray")
        badges = st.container(horizontal=True)
        badges.badge(verdict.replace("_", " "), color={"reproduced": "green", "not_reproduced": "red"}.get(verdict, "gray"))
        badges.badge("verified" if verification.get("verified") else "unverified",
                     color="green" if verification.get("verified") else "gray")
        badges.badge("grounded" if score["grounded"] else "ungrounded",
                     color="blue" if score["grounded"] else "gray")

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

        with st.popover("Share proof", icon=":material/ios_share:"):
            common.share(job)
            card = common.proof_card(job)
            if card:
                st.caption("Proof card — post-ready:")
                st.image(card, width="stretch", alt="Proof card: before and after with the verdict")
                st.download_button(
                    "Download the proof card",
                    data=card,
                    file_name=f"{job}_proof.png",
                    mime="image/png",
                    icon=":material/download:",
                )

    proof_tab, fix_tab, evidence_tab, review_tab = st.tabs(
        [":material/movie: Proof", ":material/code: Fix", ":material/rule: Evidence", ":material/fact_check: Review"]
    )

    with proof_tab:
        before, after = repro.get("before_clip", ""), proof.get("after_clip", "")
        if before and after and Path(before).exists() and Path(after).exists():
            st.caption("The same scenario, before and after — drag to compare.")
            before_after(before, after, key=f"cmp_{job}")
        else:
            st.caption("No before/after stills — screenshots need a live browser.")
        video = proof.get("proof_video")
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
        chart = common.activity_chart(summary.get("timings"))
        if chart is not None:
            st.markdown("**Pipeline timeline**")
            st.altair_chart(chart, width="stretch")
        observability = common.read_json(summary.get("artifacts", {}).get("observability", ""))
        _render_execution(observability)
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
            st.balloons()
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
        st.subheader("Ask about this run", icon=":material/forum:")
        _chat(job)


def page() -> None:
    common.init_state()
    st.title("Run review", icon=":material/fact_check:")
    jobs = store.jobs()
    if not jobs:
        common.empty_state(":material/inbox:", "No runs yet", "Submit a recording on the Runs page.")
        return
    job = st.selectbox("Run", jobs, index=0, key="run", bind="query-params")
    render(job)
