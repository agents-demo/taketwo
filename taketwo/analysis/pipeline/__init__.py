"""Pipeline orchestration — import from this package, never a concrete module.

    from taketwo.analysis import pipeline

    strategy = pipeline.resolve(agentic=True)
    result = await strategy.analyze(pipeline.Params(video_path, repo="owner/name"))
"""

from taketwo.analysis.pipeline.params import Params
from taketwo.analysis.pipeline.strategies import (
    AGENTIC,
    DETERMINISTIC,
    STRATEGIES,
    Strategy,
    default_name,
    get_strategy,
    resolve,
)

__all__ = ["AGENTIC", "DETERMINISTIC", "STRATEGIES", "Params", "Strategy", "default_name", "get_strategy", "resolve"]
