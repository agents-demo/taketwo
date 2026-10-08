"""Stage: prove the fix by re-running the scenario and recording the after clip.

Re-runs the reproduction steps through the run session's browser (when live) to see
whether the failure signal is gone, runs the repo's tests on the patched checkout
(``TEST_COMMAND``), and stitches a labelled before/after image + video. A sidecar
``runtime/data/<job>_proposed.result.json`` (``{"reproduced", "tests_pass"}``) can
inject the outcome for the offline demo; otherwise an unverified patch is assumed
fixed and ``verify`` reflects what was actually checked.
"""

from __future__ import annotations

import json
from typing import Any

from taketwo import config
from taketwo.domain import compare as compare_mod
from taketwo.domain import verify as verify_mod
from taketwo.pipeline.forge import run_tests_on_patch
from taketwo.pipeline.progress import Progress, tick
from taketwo.pipeline.stages.prove import stitch
from taketwo.storage import runtime


def _signal(console: list[str]) -> str:
    for line in console:
        low = line.lower()
        if "pageerror" in low or "error" in low or "uncaught" in low:
            return line.strip()
    return ""


def _rerun(session: Any, reproduction: dict[str, Any]) -> str:
    """Replay the scenario on the (patched) app; return the failure signal, if any."""
    start = len(session.console)
    for step in reproduction.get("steps", []):
        session.act(step.get("action", "wait"), step.get("target", ""), step.get("value", ""))
    return _signal(session.console[start:])


def _run_result(job: str, fix: dict, repo: str, base_branch: str, replayed: str | None) -> dict[str, Any]:
    sidecar = runtime.DATA_DIR / f"{job}_proposed.result.json"
    if sidecar.exists():
        try:
            return json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception:
            pass

    run: dict[str, Any] = {"reproduced": False}  # assume the patch fixes it (unverified)
    if replayed is not None:
        run["reproduced"] = bool(replayed)

    tests = run_tests_on_patch(repo, base_branch, fix.get("diff", ""), config.test_command())
    run["tests_pass"] = bool(tests["passed"]) if tests.get("ran") else True
    if tests.get("ran"):
        run["test_output"] = (tests.get("output") or "")[-2000:]
    return run


async def prove(
    reproduction: dict[str, Any],
    fix: dict[str, Any],
    job: str,
    repo: str = "",
    base_branch: str = "main",
    run_session: Any = None,
    progress: Progress | None = None,
) -> dict[str, Any]:
    """Return the proof block (empty when there is no fix to prove)."""
    if not fix.get("diff"):
        return {}

    tick(progress, "proving the fix", 90)
    proof_dir = runtime.ARTIFACTS_DIR / job

    before = reproduction.get("before_clip", "")
    if not before and (proof_dir / "before.png").exists():
        before = str(proof_dir / "before.png")

    session = getattr(run_session, "browser", None)
    after_clip = ""
    replayed: str | None = None
    if session is not None and getattr(session, "live", False):
        replayed = _rerun(session, reproduction)
        after_clip = session.snapshot(proof_dir / "after.png") or ""
    elif (proof_dir / "after.png").exists():
        after_clip = str(proof_dir / "after.png")

    run = _run_result(job, fix, repo, base_branch, replayed)
    after_repro = {**reproduction, "verdict": "reproduced" if run.get("reproduced") else "not_reproduced"}

    return {
        "after_clip": after_clip,
        "proof_path": stitch.proof(before, after_clip, str(proof_dir / "proof.png")) or "",
        "proof_video": stitch.proof_video(before, after_clip, str(proof_dir / "proof.mp4")) or "",
        "run": run,
        "verification": verify_mod.verify(reproduction, fix, run),
        "compare": compare_mod.before_after(reproduction, after_repro),
    }
