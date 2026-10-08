"""Default strategy: the fixed understand → reproduce → repair → prove → deliver run."""

from __future__ import annotations

from typing import Any

from taketwo.analysis.pipeline.params import Params
from taketwo.analysis.pipeline.strategies.base import Strategy


class DeterministicStrategy(Strategy):
    """Runs the fixed stage sequence."""

    name = "deterministic"
    description = "Fixed pipeline: understand, reproduce, repair, prove, deliver."

    async def _run(self, params: Params, progress: Any) -> tuple[str, dict]:
        return await self._run_stages(params, progress)
