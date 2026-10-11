"""Embedding surface: run a reproduction programmatically.

``replay_video`` (async) imports the pipeline lazily so importing this module does
not pull in the heavy backend. ``describe`` is the single source of truth for the
``reproduce_bug_from_video`` tool contract (used by the MCP server).
"""

from __future__ import annotations

import json
from typing import Any

from taketwo.bootstrap import run as run_async
from taketwo.storage import store

TOOL_NAME = "reproduce_bug_from_video"
TOOL_DESCRIPTION = (
    "Analyze a screen recording of a bug, reproduce it in a browser against a repo, propose a fix, "
    "and return a reproduction with evidence and a before/after proof."
)
TOOL_INPUT_PARAMS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "video_path": {"type": "string", "description": "Path to the screen recording."},
        "repo": {"type": "string", "description": "Repository as 'owner/name'."},
        "base_branch": {"type": "string", "description": "Base branch (default 'main')."},
        "app_url": {"type": "string", "description": "URL of the running app to reproduce against."},
        "agentic": {"type": "boolean", "description": "Let the model drive the run."},
    },
    "required": ["video_path"],
}


async def replay_video(
    video_path: str,
    repo: str = "",
    base_branch: str = "main",
    app_url: str = "",
    agentic: bool = False,
) -> dict[str, Any]:
    from taketwo import pipeline

    strategy = pipeline.resolve(agentic)
    return await strategy.analyze(
        pipeline.Params(video_path=video_path, repo=repo, base_branch=base_branch, app_url=app_url)
    )


def replay_video_sync(
    video_path: str,
    repo: str = "",
    base_branch: str = "main",
    app_url: str = "",
    agentic: bool = False,
) -> dict[str, Any]:
    return run_async(replay_video(video_path, repo=repo, base_branch=base_branch, app_url=app_url, agentic=agentic))


def describe() -> dict[str, Any]:
    return {"name": TOOL_NAME, "description": TOOL_DESCRIPTION, "input_params": TOOL_INPUT_PARAMS}


QA_SYSTEM = (
    "You are TakeTwo. Answer questions about a specific bug run using ONLY its stored reproduction, "
    "fix, proof and review. Be concise. Never invent steps, diffs, or verification that are not in the data."
)


def _run_context(job: str) -> dict[str, Any]:
    return {
        "reproduction": store.get_repro(job),
        "fix": store.get_fix(job),
        "proof": store.get_proof(job),
        "review": store.get_review(job),
    }


def _answer_from_data(job: str, question: str, context: dict[str, Any]) -> str:
    """Deterministic, grounded answer used when no model is configured."""
    repro, fix, proof, review = (
        context["reproduction"],
        context["fix"],
        context["proof"],
        context["review"],
    )
    q = question.lower()
    steps = repro.get("steps", [])
    if "step" in q or "reproduc" in q:
        lines = [f"{i + 1}. {s.get('action')} {s.get('target') or ''}".rstrip() for i, s in enumerate(steps)]
        return "Steps I reproduced:\n" + "\n".join(lines or ["(none inferred)"])
    if "fix" in q or "diff" in q or "patch" in q:
        return f"Proposed fix — {fix.get('summary') or '(none)'}:\n```diff\n{fix.get('diff', '') or '(no diff)'}\n```"
    if "verif" in q or "test" in q:
        verification = proof.get("verification") or {}
        return f"Verified: {verification.get('verified')} · checks: {verification.get('checks')}"
    if "review" in q or "approve" in q:
        return f"Review status: {review.get('status', 'pending')}"
    signal = repro.get("evidence", {}).get("summary") or "n/a"
    return f"Run `{job}`: verdict {repro.get('verdict', 'unclear')}; evidence: {signal}."


async def ask(job: str, question: str) -> str:
    """Answer a follow-up question about a run (grounded; falls back to the stored data)."""
    context = _run_context(job)
    prompt = f"Run data:\n{json.dumps(context, ensure_ascii=False)}\n\nQuestion: {question}"
    try:
        from taketwo.backend import run_text

        return await run_text(QA_SYSTEM, prompt)
    except Exception:
        return _answer_from_data(job, question, context)


def ask_sync(job: str, question: str) -> str:
    return run_async(ask(job, question))
