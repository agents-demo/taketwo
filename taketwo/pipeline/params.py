"""Parameters for running a reproduction strategy.

Callers pass a single ``Params`` to ``Strategy.analyze``. It carries the request and,
during the run, is populated with the inferred timeline, reproduction, fix and proof.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from taketwo.pipeline.progress import Progress


@dataclass
class Params:
    """One submission request + the run state filled in by ``Strategy.analyze``."""

    video_path: str
    repo: str = ""
    base_branch: str = "main"
    app_url: str = ""
    progress: Progress | None = None

    # populated during the run
    job: str = ""
    submission: dict = field(default_factory=dict)
    timeline: dict = field(default_factory=dict)
    reproduction: dict = field(default_factory=dict)
    fix: dict = field(default_factory=dict)
    proof: dict = field(default_factory=dict)
    delivery: dict = field(default_factory=dict)
    session: Any = None
    artifact_paths: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)
