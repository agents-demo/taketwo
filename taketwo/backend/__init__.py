"""Backend layer: the single home for everything under-the-hood of the agentic system.

The application-facing surface is small and explicit:

- ``build`` + ``TextParams`` / ``VisionParams`` â€” construct agents.
- ``run_agent`` â€” run a built agent (starts the Runner if needed).
- ``run_text`` â€” run a single-turn, tool-less text prompt (verification, Q&A).
- ``ConfigError`` â€” raised when backend config is missing/invalid.
- ``configure_logging`` â€” route openjiuwen logging.

Internally, ``backend/`` is grouped by concern: ``agent/`` (builder, params,
models, rails, tools, runner) and ``telemetry/`` (usage, traces, recorder), with
``settings.py`` and ``logs.py`` at the root. Everything there is an implementation
detail, imported only inside ``backend``. No ``from openjiuwen...`` import exists
outside this package; no application module is imported by it.
"""

from taketwo.backend.agent.builder import TextParams, VisionParams, build
from taketwo.backend.agent.runner import run_agent, run_text
from taketwo.backend.logs import configure as configure_logging
from taketwo.backend.settings import ConfigError

__all__ = [
    "ConfigError",
    "TextParams",
    "VisionParams",
    "build",
    "configure_logging",
    "run_agent",
    "run_text",
]
