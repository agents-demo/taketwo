"""The MCP tools exposed by the taketwo server."""

from __future__ import annotations

from typing import Any


def register(server: Any) -> None:
    """Attach taketwo's tools to a FastMCP ``server``."""

    @server.tool()
    def reproduce_bug_from_video(
        video_path: str,
        repo: str = "",
        base_branch: str = "main",
        app_url: str = "",
    ) -> dict:
        """Reproduce a bug from a screen recording and return the reproduction + fix."""
        from taketwo.core import service

        outcome = service.replay_video_sync(video_path, repo=repo, base_branch=base_branch, app_url=app_url)
        return {
            "job": outcome.get("job"),
            "reproduction": outcome.get("reproduction"),
            "fix": outcome.get("fix"),
            "proof": outcome.get("proof"),
        }
