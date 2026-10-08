"""Vision-agent policy for the understand stage (thin over the backend builder)."""

from __future__ import annotations

from typing import Any

from taketwo.backend import VisionParams, build
from taketwo.bootstrap import setup
from taketwo.pipeline.stages.understand import prompts
from taketwo.storage import runtime


def build_agent(*, media_dir: str, workspace: str | None = None) -> Any:
    """Build the vision DeepAgent (reads rendered frames via ``read_file``)."""
    setup()
    return build(
        VisionParams(
            system_prompt=prompts.VISION_AGENT_SYSTEM,
            workspace=workspace or str(runtime.ARTIFACTS_DIR),
            media_dir=media_dir,
        )
    )
