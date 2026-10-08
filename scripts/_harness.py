"""Shared helpers for the live end-to-end scripts (Playwright + a served app).

Not a product module: dev tooling under ``scripts/``. Requires the browser extra
(``pip install -r requirements.txt && python -m playwright install chromium``).
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taketwo.pipeline import appserver  # noqa: E402
from taketwo.pipeline.run_session import start_session  # noqa: E402
from taketwo.pipeline.stages.reproduce import replay_steps, reproduce  # noqa: E402
from taketwo.storage import runtime  # noqa: E402


def playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401

        return True
    except Exception:
        return False


def free_port() -> int:
    """An OS-assigned free TCP port (avoids clashing with lingering servers)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def serve(directory: str | Path, port: int, cwd: str | Path) -> Any:
    """Serve ``directory`` over HTTP and wait until it responds."""
    command = f'"{sys.executable}" -m http.server {port} --directory "{directory}"'
    return appserver.start(command, cwd, f"http://localhost:{port}")


async def live_reproduce(app_url: str, steps: list[dict], job: str, video_path: str) -> dict[str, Any]:
    """Drive the real reproduce stage in a live browser (no sidecars)."""
    session = start_session(job)
    reproduction = await reproduce(video_path, {"steps": steps, "failure": {}}, app_url, job, run_session=session)
    browser = getattr(session, "browser", None)
    before = (
        await browser.snapshot(runtime.ARTIFACTS_DIR / job / "before.png") if getattr(browser, "live", False) else None
    )
    return {"reproduction": reproduction, "session": session, "before": before or ""}


async def rerun(session: Any, steps: list[dict]) -> str:
    """Replay the steps again and return any new failure signal (empty = fixed)."""
    browser = session.browser
    start = len(browser.console)
    await replay_steps.replay(browser, steps)
    return replay_steps.failure_signal(browser.console[start:])
