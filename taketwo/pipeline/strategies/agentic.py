"""Opt-in strategy: the model drives the run itself.

Today it shares the stage sequence but sets the agentic flag so stages may consult
the model (grounding, localization) instead of the deterministic rules.
"""

from __future__ import annotations

from typing import Any

from taketwo.pipeline.params import Params
from taketwo.pipeline.strategies.base import Strategy


class AgenticStrategy(Strategy):
    """Model-driven run over the same stages."""

    name = "agentic"
    description = "Agent-driven pipeline: the model grounds steps and proposes the fix."

    async def _run(self, params: Params, progress: Any) -> tuple[str, dict]:
        params.state["agentic"] = True
        return await self._run_stages(params, progress)
