"""Job lifecycle: list, status, cancel, retry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/jobs")
def jobs() -> dict:
    """All known jobs (for the live "in flight" count)."""
    from taketwo.pipeline.jobs import get_runner

    return {"jobs": get_runner().jobs()}


@router.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    from taketwo.pipeline.jobs import get_runner

    status = get_runner().status(job_id)
    if status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="unknown job")
    return status


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    """Cancel a queued/running job."""
    from taketwo.pipeline.jobs import get_runner

    return {"cancelled": get_runner().cancel(job_id)}


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    """Requeue a known job with the same parameters."""
    from taketwo.pipeline.jobs import get_runner

    new_id = get_runner().retry(job_id)
    if new_id is None:
        raise HTTPException(status_code=404, detail="unknown job")
    return {"job_id": new_id, "status_url": f"/jobs/{new_id}"}
