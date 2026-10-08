"""The strategy base class and the shared stage orchestration.

A ``Strategy`` is a template: ``analyze(params)`` prepares the run (validate the
submission, start the session), runs the mode-specific ``_run``, then finalizes
(usage, job summary, exports). The shared stage sequence lives in
:meth:`_run_stages`; concrete strategies only decide how to enter it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from taketwo import config
from taketwo.bootstrap import setup
from taketwo.domain import submission as submission_mod
from taketwo.pipeline import appserver
from taketwo.pipeline.forge import ensure_repo
from taketwo.pipeline.params import Params
from taketwo.pipeline.progress import Progress, tick
from taketwo.pipeline.run_session import start_session
from taketwo.pipeline.stages.deliver import deliver
from taketwo.pipeline.stages.prove import prove
from taketwo.pipeline.stages.repair import repair
from taketwo.pipeline.stages.reproduce import reproduce
from taketwo.pipeline.stages.understand import understand
from taketwo.storage import json_store, runtime, store


class Strategy:
    """Base reproduction strategy (template method)."""

    name: str = ""
    description: str = ""

    async def analyze(self, params: Params) -> dict[str, Any]:
        self._prepare(params)
        try:
            result, extras = await self._run(params, params.progress)
            return await self._finalize(params, result, extras, params.progress)
        finally:
            appserver.stop(params.state.get("app"))

    # -- template steps (override _run) ----------------------------------- #
    async def _run(self, params: Params, progress: Progress | None) -> tuple[Any, dict]:
        """Run the mode-specific stages; return (text result, patch extras)."""
        raise NotImplementedError

    # -- shared prologue -------------------------------------------------- #
    def _prepare(self, params: Params) -> None:
        progress = params.progress
        tick(progress, "preparing", 2)
        setup()

        submission = submission_mod.normalize(
            {
                "video_path": params.video_path,
                "repo": params.repo,
                "base_branch": params.base_branch,
                "app_url": params.app_url,
            }
        )
        problems = submission_mod.validate(submission)
        if problems:
            raise ValueError("; ".join(problems))
        if not Path(params.video_path).exists():
            raise FileNotFoundError(f"recording not found: {params.video_path}")

        params.submission = submission
        params.job = submission_mod.job_id(submission)
        store.set_current_job(params.job)
        params.session = start_session(params.job)

    # -- shared stage sequence -------------------------------------------- #
    async def _run_stages(self, params: Params, progress: Progress | None) -> tuple[str, dict]:
        # Stage order (authoritative list: ``pipeline.STAGES``):
        # understand -> reproduce -> repair -> prove -> deliver
        agent = params.session.vision_agent if params.session else None

        params.timeline = await understand(params.video_path, progress, agent=agent)

        app_url = self._start_app(params)
        reproduction = await reproduce(
            params.video_path, params.timeline, app_url, params.job, progress, run_session=params.session
        )
        store.save_repro(params.job, reproduction)
        params.reproduction = reproduction

        fix = await repair(reproduction, params.repo, params.job, progress)
        store.save_fix(params.job, fix)
        params.fix = fix

        proof = await prove(
            reproduction,
            fix,
            params.job,
            repo=params.repo,
            base_branch=params.base_branch,
            run_session=params.session,
            progress=progress,
        )
        store.save_proof(params.job, proof)
        params.proof = proof

        params.delivery = deliver(params.submission, reproduction, fix, proof, progress)

        return self._summary(reproduction, fix, proof), {"observations": params.timeline}

    def _start_app(self, params: Params) -> str:
        """Serve the app from the repo when no ``app_url`` was given (best-effort)."""
        if params.app_url:
            return params.app_url
        if not (params.repo and config.app_start_command()):
            return ""
        repo_dir = ensure_repo(params.repo, params.base_branch)
        app = appserver.start(config.app_start_command(), repo_dir, config.app_url())
        params.state["app"] = app
        return app.url if app else ""

    def _summary(self, reproduction: dict, fix: dict, proof: dict) -> str:
        verdict = reproduction.get("verdict", "unclear")
        lines = [f"reproduction: {verdict}"]
        if reproduction.get("evidence", {}).get("summary"):
            lines.append(f"signal: {reproduction['evidence']['summary']}")
        lines.append(f"fix: {fix.get('summary') or '(none)'}")
        if proof.get("proof_path"):
            lines.append(f"proof: {proof['proof_path']}")
        return "\n".join(lines)

    # -- shared epilogue -------------------------------------------------- #
    async def _finalize(
        self,
        params: Params,
        result: Any,
        extras: dict,
        progress: Progress | None,
    ) -> dict[str, Any]:
        usage = params.session.usage_summary() if params.session else {}
        if params.session is not None and (path := params.session.save_details()):
            params.artifact_paths["observability"] = path

        timings: list = []
        if progress is not None:
            try:
                timings = progress.snapshot().get("timings") or []
            except Exception:
                timings = []

        summary = {
            "job": params.job,
            "submission": params.submission,
            "timeline": params.timeline,
            "reproduction": params.reproduction,
            "fix": params.fix,
            "proof": params.proof,
            "delivery": params.delivery,
            "usage": usage,
            "artifacts": params.artifact_paths,
            "timings": timings,
        }
        summary_path = runtime.ARTIFACTS_DIR / f"{params.job}_summary.json"
        try:
            json_store.write_json(summary_path, summary)
        except Exception:
            summary_path = None

        tick(progress, "done", 100)
        return {
            "result": result,
            "job": params.job,
            "submission": params.submission,
            "timeline": params.timeline,
            "reproduction": params.reproduction,
            "fix": params.fix,
            "proof": params.proof,
            "delivery": params.delivery,
            "usage": usage,
            "timings": timings,
            "summary_path": str(summary_path) if summary_path else "",
        }
