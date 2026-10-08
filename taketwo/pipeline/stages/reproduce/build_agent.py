"""Text-agent policy for grounding inferred steps onto live elements."""

from __future__ import annotations

from typing import Any

from taketwo.backend import TextParams, build
from taketwo.bootstrap import setup
from taketwo.pipeline.stages.reproduce import prompts
from taketwo.storage import runtime


def build_agent(*, accumulator: dict | None = None, max_iterations: int = 8) -> Any:
    """Build the reproduction agent (returns the build result: agent + recorder)."""
    setup()
    return build(
        TextParams(
            system_prompt=prompts.REPRODUCE_AGENT_SYSTEM,
            tools=[],
            rails=[],
            max_iterations=max_iterations,
            workspace=runtime.workspace(),
            recorder=accumulator,
        )
    )
