"""Per-session state defaults and reviewer identity."""

from __future__ import annotations

import streamlit as st


def init_state() -> None:
    st.session_state.setdefault("job_id", None)
    st.session_state.setdefault("refreshed_for", None)
    st.session_state.setdefault("last_submission", None)
    st.session_state.setdefault("opened_for", None)


def actor() -> str:
    """Who is reviewing — from OIDC (``st.user``) when signed in, else the local operator."""
    user = getattr(st, "user", None)
    for attr in ("email", "name"):
        value = getattr(user, attr, None)
        if value:
            return str(value)
    return "maintainer (local)"
