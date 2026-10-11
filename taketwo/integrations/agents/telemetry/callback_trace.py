"""Usage capture via the Runner's callback framework (every model call)."""

from __future__ import annotations

from typing import Any

from taketwo.integrations.agents.telemetry.usage import extract_usage, summarize


class CallbackTrace:
    """Capture usage for every model call via the Runner's callback framework.

    A lighter-weight, framework-native alternative/supplement to ``attach``; it
    observes the global LLM-invoke-output event so both vision and text calls are
    covered without wrapping each model.
    """

    def __init__(self) -> None:
        self.usages: list[dict] = []

    def install(self) -> bool:
        """Register the observer. Returns ``False`` if unavailable (never raises)."""
        from taketwo.integrations.agents.agent.runner import on_llm_output

        async def _observe(*args: Any, **kwargs: Any) -> None:
            for obj in list(args) + list(kwargs.values()):
                record = extract_usage(obj)
                if record:
                    self.usages.append(record)
                    return

        return on_llm_output(_observe)

    def summary(self) -> dict:
        return summarize(self.usages)
