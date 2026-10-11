"""The agent builder entry point: build the agent described by a params object."""

from __future__ import annotations

from taketwo.integrations.agents import settings as backend_settings
from taketwo.integrations.agents.agent.builder.base import AgentBuilder
from taketwo.integrations.agents.agent.builder.params import Params, VisionParams
from taketwo.integrations.agents.agent.builder.result import BuildResult
from taketwo.integrations.agents.agent.builder.text import TextBuilder
from taketwo.integrations.agents.agent.builder.vision import VisionBuilder


def _select(params: Params) -> AgentBuilder:
    return VisionBuilder(params) if isinstance(params, VisionParams) else TextBuilder(params)


def build(params: Params) -> BuildResult:
    """Build the agent described by ``params``.

    Validates backend config, selects the text/vision builder (which owns the run
    recorder and model instrumentation), and returns the agent + recorder.
    """
    backend_settings.validate()
    builder = _select(params)
    return BuildResult(agent=builder.build(), recorder=builder.recorder)
