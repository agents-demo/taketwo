"""Local state: one set of JSON files per submitted job.

A job is identified by :func:`taketwo.domain.submission.job_id`; its artifacts live
at ``runtime/data/<job>_repro.json``, ``<job>_fix.json``, ``<job>_proof.json``.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from taketwo.storage import json_store, runtime

DATA_DIR = runtime.DATA_DIR
REPRO_SUFFIX = "_repro.json"
FIX_SUFFIX = "_fix.json"
PROOF_SUFFIX = "_proof.json"

_current_job: str | None = None


def set_current_job(job: str) -> str:
    """Remember which job the next saved artifacts belong to."""
    global _current_job
    _current_job = job
    return job


def current_job() -> str | None:
    return _current_job


def _path(job: str, suffix: str) -> Path:
    return DATA_DIR / f"{job}{suffix}"


def _save(job: str, suffix: str, data: dict[str, Any]) -> dict[str, Any]:
    json_store.write_json(_path(job, suffix), data)
    return data


def save_repro(job: str, reproduction: dict[str, Any]) -> dict[str, Any]:
    return _save(job, REPRO_SUFFIX, reproduction)


def get_repro(job: str) -> dict[str, Any]:
    return json_store.read_json(_path(job, REPRO_SUFFIX), {})


def save_fix(job: str, fix: dict[str, Any]) -> dict[str, Any]:
    return _save(job, FIX_SUFFIX, fix)


def get_fix(job: str) -> dict[str, Any]:
    return json_store.read_json(_path(job, FIX_SUFFIX), {})


def save_proof(job: str, proof: dict[str, Any]) -> dict[str, Any]:
    return _save(job, PROOF_SUFFIX, proof)


def get_proof(job: str) -> dict[str, Any]:
    return json_store.read_json(_path(job, PROOF_SUFFIX), {})


def patch_repro(job: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    """Merge ``patch`` into a job's reproduction file, if it exists."""
    path = _path(job, REPRO_SUFFIX)
    if not path.exists():
        return None
    data = json_store.read_json(path, {})
    if not isinstance(data, dict):
        return None
    data.update(patch)
    return json_store.write_json(path, data) or data


def jobs() -> list[str]:
    """All job ids, newest first (by repro file mtime)."""
    paths = sorted(DATA_DIR.glob(f"*{REPRO_SUFFIX}"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name[: -len(REPRO_SUFFIX)] for p in paths]


def latest() -> str | None:
    """The most recently written job id, or ``None``."""
    found = jobs()
    return found[0] if found else None


def find(job: str) -> dict[str, Any] | None:
    """The reproduction for ``job`` (or a fuzzy match), or ``None``."""
    if not job:
        return None
    path = _path(job, REPRO_SUFFIX)
    if path.exists():
        return json_store.read_json(path, {})
    matches = [j for j in jobs() if job in j]
    return get_repro(matches[0]) if matches else None


def delete_job(job: str) -> bool:
    """Delete a job's JSON state, artifacts and cache."""
    removed = False
    for suffix in (REPRO_SUFFIX, FIX_SUFFIX, PROOF_SUFFIX):
        path = _path(job, suffix)
        if path.exists():
            path.unlink()
            removed = True
    for base in (runtime.ARTIFACTS_DIR, runtime.CACHE_DIR):
        target = base / job
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
    return removed


def reset() -> None:
    for suffix in (REPRO_SUFFIX, FIX_SUFFIX, PROOF_SUFFIX):
        for path in DATA_DIR.glob(f"*{suffix}"):
            path.unlink()
