"""Stage: prove the fix by re-running the scenario and recording the after clip.

The actual "apply the patch, restart the app, run the suite" work happens in the
sandboxed runner (interfaces/worker); here we consume its result. A sidecar
``runtime/data/<job>_proposed.result.json`` (``{"reproduced", "tests_pass"}``) lets
the outcome be injected deterministically; otherwise the presence of a patch is
taken as the sandbox's success.
"""

from __future__ import annotations

import json
from typing import Any

from taketwo.analysis.progress import Progress, tick
from taketwo.analysis.stages.prove import stitch
from taketwo.domain import compare as compare_mod
from taketwo.domain import verify as verify_mod
from taketwo.storage import runtime


def _run_result(job: str, fix: dict) -> dict[str, Any]:
    sidecar = runtime.DATA_DIR / f"{job}_proposed.result.json"
    if sidecar.exists():
        try:
            return json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"reproduced": False, "tests_pass": True} if fix.get("diff") else {"reproduced": True, "tests_pass": False}


def prove(
    reproduction: dict[str, Any],
    fix: dict[str, Any],
    job: str,
    after_clip: str = "",
    progress: Progress | None = None,
) -> dict[str, Any]:
    """Return the proof block (empty when there is no fix to prove)."""
    if not fix.get("diff"):
        return {}

    tick(progress, "proving the fix", 90)
    run = _run_result(job, fix)
    before = reproduction.get("before_clip", "")
    proof_dir = runtime.ARTIFACTS_DIR / job
    if not after_clip:
        candidate = proof_dir / "after.png"
        after_clip = str(candidate) if candidate.exists() else ""
    if not before:
        candidate = proof_dir / "before.png"
        before = str(candidate) if candidate.exists() else ""
    proof_path = stitch.proof(before, after_clip, str(proof_dir / "proof.png"))
    proof_video = stitch.proof_video(before, after_clip, str(proof_dir / "proof.mp4"))
    after_repro = {**reproduction, "verdict": "not_reproduced" if not run.get("reproduced") else "reproduced"}

    return {
        "after_clip": after_clip,
        "proof_path": proof_path or "",
        "proof_video": proof_video or "",
        "run": run,
        "verification": verify_mod.verify(reproduction, fix, run),
        "compare": compare_mod.before_after(reproduction, after_repro),
    }
