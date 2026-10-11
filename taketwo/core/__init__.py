"""The pipeline — the workflow of five stages, run by two interchangeable strategies.

- :mod:`~taketwo.core.stages.understand` — recording → timeline + failure.
- :mod:`~taketwo.core.stages.reproduce` — timeline → reproduced run + evidence.
- :mod:`~taketwo.core.stages.repair` — evidence → localized cause + patch.
- :mod:`~taketwo.core.stages.prove` — patch → after clip + before/after proof.
- :mod:`~taketwo.core.stages.deliver` — artifacts → issue + draft PR.
- :mod:`~taketwo.core.strategies` — deterministic / agentic modes over the stages.

Import the orchestrator from this package, never a concrete strategy module:

    from taketwo import core

    strategy = core.resolve(agentic=True)
    result = await strategy.analyze(core.Params(video_path, repo="owner/name"))

Side-effect free.
"""

from taketwo.core.params import Params
from taketwo.core.stages import STAGES
from taketwo.core.strategies import (
    AGENTIC,
    DETERMINISTIC,
    STRATEGIES,
    Strategy,
    default_name,
    get_strategy,
    resolve,
)

__all__ = [
    "AGENTIC",
    "DETERMINISTIC",
    "STAGES",
    "STRATEGIES",
    "Params",
    "Strategy",
    "default_name",
    "get_strategy",
    "resolve",
]
