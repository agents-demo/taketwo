"""The run header: status badges, key metrics, and the share popover."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from taketwo.surfaces.gui1 import data, share


def render(job: str, repro: dict, proof: dict, review: dict, summary: dict, score: dict) -> None:
    usage = summary.get("usage") or {}
    submission = summary.get("submission") or {}
    verification = proof.get("verification") or {}
    verdict = repro.get("verdict", "unclear")

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
                f":material/schedule: {data.when(job)}",
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
            share.share(job)
            card = share.proof_card(job)
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
