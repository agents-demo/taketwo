"""Stdio MCP server exposing ``reproduce_bug_from_video`` to MCP clients.

Wrapping is MCP-native (FastMCP's ``@server.tool``); the tool decorator stays inside
the backend.

    python -m taketwo.interfaces.mcp.server
"""

from __future__ import annotations

from taketwo.bootstrap import setup


def main() -> None:
    setup()
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("MCP deps missing: pip install -r requirements.txt") from exc

    server = FastMCP("taketwo")

    @server.tool()
    def reproduce_bug_from_video(
        video_path: str,
        repo: str = "",
        base_branch: str = "main",
        app_url: str = "",
    ) -> dict:
        """Reproduce a bug from a screen recording and return the reproduction + fix."""
        from taketwo.interfaces import service

        outcome = service.replay_video_sync(video_path, repo=repo, base_branch=base_branch, app_url=app_url)
        return {
            "job": outcome.get("job"),
            "reproduction": outcome.get("reproduction"),
            "fix": outcome.get("fix"),
            "proof": outcome.get("proof"),
        }

    server.run()


if __name__ == "__main__":
    main()
