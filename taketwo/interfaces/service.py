"""Embedding surface: run a reproduction programmatically.

``replay_video`` (async) imports the pipeline lazily so importing this module does
not pull in the heavy backend. ``describe`` is the single source of truth for the
``reproduce_bug_from_video`` tool contract (used by the MCP server).
"""

from __future__ import annotations

from typing import Any

from taketwo.bootstrap import run as run_async

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
