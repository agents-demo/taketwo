"""Text-agent policy for the repair stage (repo tools + fix prompt)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from taketwo.analysis.stages.repair import prompts, repo_tools
from taketwo.backend import TextParams, build
from taketwo.bootstrap import setup
from taketwo.storage import runtime


def build_agent(
    *,
    repo_dir: str,
    rails: Sequence[str] | None = None,
    recorder: Any = None,
    tools: list | None = None,
    system_prompt: str | None = None,
    max_iterations: int = 15,
) -> Any:
    """Build the repair DeepAgent (returns the build result: agent + recorder)."""
    setup()
    return build(
        TextParams(
            system_prompt=system_prompt or prompts.REPAIR_AGENT_SYSTEM,
            tools=tools if tools is not None else repo_tools.make_tools(repo_dir),
            rails=list(rails) if rails else [],
            max_iterations=max_iterations,
            workspace=runtime.workspace(),
            recorder=recorder,
        )
    )
