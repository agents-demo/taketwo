"""The agents integration — the single home for everything under-the-hood of the agentic system.

The application-facing surface is small and explicit:

- ``build`` + ``TextParams`` / ``VisionParams`` — construct agents.
- ``run_agent`` — run a built agent (starts the Runner if needed).
- ``run_text`` — run a single-turn, tool-less text prompt (verification, Q&A).
- ``ConfigError`` — raised when model config is missing/invalid.
- ``configure_logging`` — route openjiuwen logging.

Internally this package is grouped by concern: ``agent/`` (builder, params,
models, rails, tools, runner) and ``telemetry/`` (usage, traces, recorder), with
``settings.py`` and ``logs.py`` at the root. Everything here is an implementation
detail, imported only inside this package. No ``from openjiuwen...`` import exists
outside it; no application module is imported by it.
"""

from taketwo.integrations.agents.agent.builder import TextParams, VisionParams, build
from taketwo.integrations.agents.agent.runner import run_agent, run_text
from taketwo.integrations.agents.logs import configure as configure_logging
from taketwo.integrations.agents.settings import ConfigError

__all__ = [
    "ConfigError",
    "TextParams",
    "VisionParams",
    "build",
    "configure_logging",
    "run_agent",
    "run_text",
]
