"""The execution timeline: model + tool calls in order, with I/O and latency."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_execution(observability: dict) -> None:
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
        if event.get("probe"):
            title = "↳ image-support probe · framework self-check (not a real step)"
        else:
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
