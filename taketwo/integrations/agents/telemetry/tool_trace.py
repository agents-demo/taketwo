"""Tool-call tracing: name, arguments, result and duration, via callback events."""

from __future__ import annotations

import time
from typing import Any

from taketwo.integrations.agents.telemetry.sanitize import _as_text, _tool_arguments
from taketwo.integrations.agents.telemetry.sequence import next_seq


class ToolTrace:
    """Records tool calls (name, arguments, result, duration) via callback events.

    openjiuwen's tool lifecycle fires ``TOOL_CALL_STARTED``/``TOOL_CALL_FINISHED``
    (and ``TOOL_CALL_ERROR``) with ``tool_name``/``tool_id``/``inputs``/``result``.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._open: dict[Any, dict] = {}

    def install(self) -> bool:
        """Register the observers. Returns ``False`` if unavailable (never raises)."""
        from taketwo.integrations.agents.agent.runner import on_tool_calls

        async def _started(*args: Any, **kwargs: Any) -> None:
            key = kwargs.get("tool_id") or kwargs.get("tool_name")
            self._open[key] = {
                "name": str(kwargs.get("tool_name") or ""),
                "arguments": _tool_arguments(kwargs.get("inputs")),
                "started": time.monotonic(),
                "seq": next_seq(),
            }

        async def _finished(*args: Any, **kwargs: Any) -> None:
            key = kwargs.get("tool_id") or kwargs.get("tool_name")
            rec = self._open.pop(key, None) or {
                "name": str(kwargs.get("tool_name") or ""),
                "arguments": "",
                "started": time.monotonic(),
                "seq": next_seq(),
            }
            rec["seconds"] = round(time.monotonic() - rec.get("started", time.monotonic()), 2)
            rec["result"] = _as_text(kwargs.get("result"), 4000)
            self.calls.append(rec)

        async def _error(*args: Any, **kwargs: Any) -> None:
            key = kwargs.get("tool_id") or kwargs.get("tool_name")
            rec = self._open.pop(key, None)
            if rec is None:
                return
            rec["seconds"] = round(time.monotonic() - rec.get("started", time.monotonic()), 2)
            rec["error"] = str(kwargs.get("error"))
            self.calls.append(rec)

        return on_tool_calls(_started, _finished, _error)

    def records(self) -> list[dict]:
        return [dict(c) for c in self.calls]
