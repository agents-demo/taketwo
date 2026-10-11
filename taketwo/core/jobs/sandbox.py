"""Build the worker command: a local ``python -m`` run, or a sandboxed Docker run.

When ``SANDBOX_IMAGE`` is set the worker runs inside Docker (dropped capabilities,
resource limits, only the forwarded env), so untrusted jobs are isolated.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Environment variables forwarded into the sandbox container (``-e KEY``).
FORWARD_ENV = (
    "API_KEY",
    "API_BASE",
    "MODEL_NAME",
    "MODEL_PROVIDER",
    "VISION_MODEL_NAME",
    "LLM_TEMPERATURE",
    "VISION_TEMPERATURE",
    "LLM_TIMEOUT",
    "LLM_RETRIES",
    "GITHUB_TOKEN",
    "GITHUB_WEBHOOK_SECRET",
    "TEST_COMMAND",
    "APP_START_COMMAND",
    "PATCHED_APP_URL",
)


def command(job: dict[str, Any]) -> list[str]:
    """The argv to run the worker for ``job`` (local python, or Docker)."""
    worker = [
        "-m",
        "taketwo.core.jobs.worker",
        job["video_path"],
        "--progress",
        job["progress_path"],
        "--repo",
        job["repo"],
        "--branch",
        job["base_branch"],
        "--app",
        job["app_url"],
    ]
    if job["agentic"]:
        worker.append("--agentic")

    image = os.getenv("SANDBOX_IMAGE", "").strip()
    if not image:
        return [sys.executable, *worker]

    cwd = str(Path.cwd())
    env_args: list[str] = []
    for key in FORWARD_ENV:
        env_args += ["-e", key]
    return [
        "docker", "run", "--rm",
        "--cpus", os.getenv("SANDBOX_CPU", "1"),
        "--memory", os.getenv("SANDBOX_MEMORY", "1g"),
        "--pids-limit", os.getenv("SANDBOX_PIDS", "512"),
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "-v", f"{cwd}:{cwd}", "-w", cwd,
        *env_args,
        image, "python", *worker,
    ]
