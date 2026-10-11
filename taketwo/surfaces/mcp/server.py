"""Stdio MCP server exposing taketwo's tools to MCP clients.

    python -m taketwo.surfaces.mcp.server

The tool definitions live in :mod:`taketwo.surfaces.mcp.tools`.
"""

from __future__ import annotations

from taketwo.bootstrap import setup


def main() -> None:
    setup()
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("MCP deps missing: pip install -r requirements.txt") from exc

    from taketwo.surfaces.mcp.tools import register

    server = FastMCP("taketwo")
    register(server)
    server.run()


if __name__ == "__main__":
    main()
