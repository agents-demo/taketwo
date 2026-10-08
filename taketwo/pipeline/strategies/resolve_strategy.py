"""The strategy registry and factory.

Callers obtain a strategy here (by name or via :func:`resolve`); they never import a
concrete strategy module. To add one, subclass ``Strategy`` and register it.
"""

from __future__ import annotations

from taketwo import config
from taketwo.pipeline.strategies.agentic import AgenticStrategy
from taketwo.pipeline.strategies.base import Strategy
from taketwo.pipeline.strategies.deterministic import DeterministicStrategy

DETERMINISTIC = "deterministic"
AGENTIC = "agentic"

STRATEGIES: dict[str, Strategy] = {
    DETERMINISTIC: DeterministicStrategy(),
    AGENTIC: AgenticStrategy(),
}


def default_name() -> str:
    """The configured default strategy name (``AGENTIC_MODE``)."""
    return AGENTIC if config.agentic_mode() else DETERMINISTIC


def get_strategy(name: str | None = None) -> Strategy:
    """Look up a strategy by name, or the configured default when ``name`` is ``None``."""
    resolved = name or default_name()
    try:
        return STRATEGIES[resolved]
    except KeyError:
        known = ", ".join(sorted(STRATEGIES))
        raise ValueError(f"unknown strategy {resolved!r}; known: {known}") from None


def resolve(agentic: bool = False) -> Strategy:
    """The strategy for a request: agentic when requested, else the configured default."""
    return get_strategy(AGENTIC if agentic else default_name())
