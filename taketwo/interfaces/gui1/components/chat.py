"""The grounded follow-up chat for a run."""

from __future__ import annotations

import streamlit as st

from taketwo.pipeline import service


def chat(job: str) -> None:
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
