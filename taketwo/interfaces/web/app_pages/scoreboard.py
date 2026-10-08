"""Scoreboard: the public reproduce rate and the runs worth bragging about."""

from __future__ import annotations

import streamlit as st

from taketwo.interfaces.web import common


def page() -> None:
    common.init_state()
    st.title("Scoreboard", icon=":material/emoji_events:")
    st.caption("The reproduce rate, in the open — and the runs worth showing off.")

    rows = common.rows(None)
    if not rows:
        common.empty_state(
            ":material/emoji_events:", "Nothing scored yet", "Run a reproduction to start the scoreboard."
        )
        return

    total = len(rows)
    verified = sum(1 for r in rows if r["verified"])
    approved = sum(1 for r in rows if r["review"] == "approved")
    rate = common.reproduce_rate(rows)

    metrics = st.columns(4)
    metrics[0].metric("Reproduce rate", f"{rate:.0%}")
    metrics[1].metric("Verified", verified)
    metrics[2].metric("Approved", approved)
    metrics[3].metric("Runs", total)
    st.progress(rate, text=f"Reproduce rate — {rate:.0%} of clips became a reproduction")

    trend = common.rate_trend(rows)
    if trend is not None:
        st.altair_chart(trend, width="stretch")

    st.space("medium")
    st.subheader("Hall of fame", icon=":material/military_tech:")
    top = sorted(rows, key=lambda r: (r["verified"], r["score"]), reverse=True)[:10]
    common.runs_dataframe(top)

    st.space("medium")
    st.subheader("Repos", icon=":material/folder_special:")
    repos: dict[str, dict] = {}
    for row in rows:
        entry = repos.setdefault(row["repo"], {"repo": row["repo"], "runs": 0, "reproduced": 0, "verified": 0})
        entry["runs"] += 1
        entry["reproduced"] += int(row["verdict"] == "reproduced")
        entry["verified"] += int(row["verified"])
    board = sorted(repos.values(), key=lambda d: (d["reproduced"] / d["runs"], d["runs"]), reverse=True)
    for entry in board:
        entry["rate"] = entry["reproduced"] / entry["runs"]
    st.dataframe(
        board,
        hide_index=True,
        width="stretch",
        column_config={
            "repo": st.column_config.TextColumn("Repo", width="large"),
            "runs": st.column_config.NumberColumn("Runs"),
            "reproduced": st.column_config.NumberColumn("Reproduced"),
            "verified": st.column_config.NumberColumn("Verified"),
            "rate": st.column_config.ProgressColumn("Rate", min_value=0.0, max_value=1.0, format="%.0%"),
        },
        alt="Reproduce rate by repository",
    )

    st.space("medium")
    share_col, card_col = st.columns(2)
    with share_col.popover("Share the top run", icon=":material/ios_share:"):
        common.share(top[0]["run"])

    card = common.share_card(rows)
    if card:
        with card_col.popover("Share the score card", icon=":material/insights:"):
            st.image(card, width="stretch", alt="TakeTwo score card with the reproduce rate")
            st.download_button(
                "Download the card",
                data=card,
                file_name="taketwo_scorecard.png",
                mime="image/png",
                icon=":material/download:",
            )
