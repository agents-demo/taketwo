"""Full-pipeline integration test (needs a model endpoint + a running app).

Skipped unless ``TAKETWO_APP_URL`` and model credentials are present, so the offline
suite stays green. The sandboxed runner (``interfaces/runner.py``) drives the same
scenario in CI with a Docker image.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

requires = pytest.mark.skipif(
    not (
        os.getenv("API_KEY")
        and os.getenv("API_BASE")
        and os.getenv("MODEL_NAME")
        and os.getenv("TAKETWO_APP_URL")
    ),
    reason="needs model credentials (API_KEY/API_BASE/MODEL_NAME) and TAKETWO_APP_URL",
)


@requires
def test_reproduces_sample_bug(tmp_path):
    from taketwo.bootstrap import run
    from taketwo.pipeline import pipeline

    video = tmp_path / "bug.mov"
    video.write_bytes(b"placeholder")
    strategy = pipeline.resolve()
    outcome = run(
        strategy.analyze(
            pipeline.Params(video_path=str(video), app_url=os.environ["TAKETWO_APP_URL"])
        )
    )
    assert outcome["reproduction"]["verdict"] in {"reproduced", "not_reproduced", "unclear"}
