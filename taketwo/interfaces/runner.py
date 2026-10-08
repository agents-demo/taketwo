"""Sandboxed job runner: run reproduction jobs in separate processes.

Each job runs ``taketwo.interfaces.worker`` in its own subprocess (progress streamed to
a temp JSON file), optionally wrapped in Docker when ``SANDBOX_IMAGE`` is set, so
concurrent and untrusted jobs are isolated from the serving process.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from taketwo.storage import runtime

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


def _read_progress(path: str) -> dict[str, Any]:
    try:
        file = Path(path)
        return json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
    except Exception:
        return {}


class Runner:
    """A small job queue that runs workers in a bounded thread pool of subprocesses."""

    def __init__(self, max_workers: int | None = None) -> None:
        workers = max_workers or int(os.getenv("RUNNER_WORKERS", "1"))
        self._pool = ThreadPoolExecutor(max_workers=max(1, workers))
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def submit(
        self,
        *,
        video_path: str,
        repo: str = "",
        base_branch: str = "main",
        app_url: str = "",
        agentic: bool = False,
    ) -> str:
        job_id = uuid.uuid4().hex[:12]
        job = {
            "id": job_id,
            "status": "queued",
            "video_path": video_path,
            "repo": repo,
            "base_branch": base_branch,
            "app_url": app_url,
            "agentic": agentic,
            "progress_path": str(Path(tempfile.gettempdir()) / f"taketwo_{job_id}.json"),
            "error": None,
        }
        with self._lock:
            self._jobs[job_id] = job
        self._pool.submit(self._run, job)
        return job_id

    def shutdown(self, wait: bool = False) -> None:
        """Stop accepting jobs and release the worker threads."""
        self._pool.shutdown(wait=wait, cancel_futures=True)

    def status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            return {"status": "unknown", "id": job_id}

        info = dict(job)
        progress = _read_progress(job["progress_path"])
        if progress:
            info["progress"] = progress
            stem = progress.get("stem")
            if stem:
                summary = runtime.ARTIFACTS_DIR / f"{stem}_summary.json"
                if summary.exists():
                    info["summary_path"] = str(summary)
        return info

    def _run(self, job: dict[str, Any]) -> None:
        job["status"] = "running"
        try:
            code = subprocess.run(self._command(job), check=False).returncode
            job["status"] = "done" if code == 0 else "failed"
            if code != 0:
                job["error"] = f"worker exited {code}"
        except Exception as exc:  # pragma: no cover - depends on environment
            job["status"] = "failed"
            job["error"] = str(exc)

    def _command(self, job: dict[str, Any]) -> list[str]:
        worker = [
            "-m",
            "taketwo.interfaces.worker",
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
            "-v", f"{cwd}:{cwd}", "-w", cwd,
            *env_args,
            image, "python", *worker,
        ]


_runner: Runner | None = None
_runner_lock = threading.Lock()


def get_runner() -> Runner:
    """The process-wide runner singleton."""
    global _runner
    if _runner is None:
        with _runner_lock:
            if _runner is None:
                _runner = Runner()
    return _runner
