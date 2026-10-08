"""The pipeline — the workflow of five stages, run by two interchangeable strategies.

- :mod:`~taketwo.pipeline.stages.understand` — recording → timeline + failure.
- :mod:`~taketwo.pipeline.stages.reproduce` — timeline → reproduced run + evidence.
- :mod:`~taketwo.pipeline.stages.repair` — evidence → localized cause + patch.
- :mod:`~taketwo.pipeline.stages.prove` — patch → after clip + before/after proof.
- :mod:`~taketwo.pipeline.stages.deliver` — artifacts → issue + draft PR.
- :mod:`~taketwo.pipeline.strategies` — deterministic / agentic modes over the stages.

Import the orchestrator from this package, never a concrete strategy module:

    from taketwo import pipeline

    strategy = pipeline.resolve(agentic=True)
    result = await strategy.analyze(pipeline.Params(video_path, repo="owner/name"))

Side-effect free.
"""

from taketwo.pipeline.params import Params
from taketwo.pipeline.stages import STAGES
from taketwo.pipeline.strategies import (
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
