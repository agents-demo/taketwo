"""Record a demo scenario as a real ~5 s video clip.

Uses Playwright's built-in recorder: it drives the scenario's steps in a real browser
*while recording*, then transcodes the recording to ``scenarios/<name>/clip.mp4`` (no
timeline sidecar, so ``understand`` has to watch the video).

    python demos/maintenance/record_video.py [scenario]          # default: booking
"""

from __future__ import annotations

import json
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # demos/ (for _scenario)

from _scenario import app_dir, clip, load  # noqa: E402

INTRO_MS = 800  # hold on the initial page
PACE_MS = 1200  # pause after each step
OUTRO_MS = 800  # hold at the end


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401

        return True
    except Exception:
        return False


def _serve(directory: Path, cwd: Path) -> Any:
    from taketwo.integrations import appserver

    port = _free_port()
    command = f'"{sys.executable}" -m http.server {port} --directory "{directory}"'
    return appserver.start(command, str(cwd), f"http://localhost:{port}")


def _run_step(page: Any, step: dict) -> None:
    action, target = step.get("action"), step.get("target")
    try:
        if action == "click" and target:
            page.click(target)
        elif action == "fill" and target:
            page.fill(target, str(step.get("value", "")))
        elif action == "goto" and target:
            page.goto(target)
        elif action == "wait":
            page.wait_for_timeout(300)
    except Exception:
        pass


def _record(url: str, steps: list[dict], work: Path) -> Path:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 960, "height": 640},
            record_video_dir=str(work),
            record_video_size={"width": 960, "height": 640},
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(INTRO_MS)
        for step in steps:
            _run_step(page, step)
            page.wait_for_timeout(PACE_MS)
        page.wait_for_timeout(OUTRO_MS)
        webm = Path(page.video.path())
        context.close()  # flushes the recording
        browser.close()
    return webm


def _to_mp4(webm: Path, out: Path) -> int:
    import imageio.v2 as iio
    import numpy as np

    reader = iio.get_reader(str(webm), "ffmpeg")
    fps = float(reader.get_meta_data().get("fps", 25) or 25)
    count = 0
    with iio.get_writer(str(out), fps=fps) as writer:
        for frame in reader:
            writer.append_data(np.asarray(frame))
            count += 1
    return count


def main(name: str = "booking") -> int:
    from taketwo.core.bootstrap import setup
    from taketwo.integrations import appserver

    setup()
    if not _playwright_available():
        print("Playwright not installed.  python -m playwright install chromium")
        return 2

    root = Path(__file__).resolve().parents[2]
    app = _serve(app_dir(name), root)
    work = Path(tempfile.mkdtemp(prefix=f"taketwo_rec_{name}_"))
    try:
        if not app:
            print("could not start the demo app")
            return 1
        webm = _record(app.url, load(name)["steps"], work)
    finally:
        appserver.stop(app)

    frames = _to_mp4(webm, clip(name))
    # A timeline sidecar makes the demo reproduce deterministically (no vision guess).
    Path(f"{clip(name)}.timeline.json").write_text(
        json.dumps({"steps": load(name)["steps"], "failure": {}}, indent=2), encoding="utf-8"
    )
    shutil.rmtree(work, ignore_errors=True)
    print(f"clip: {clip(name)}  ({frames} frames)")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(main(args[0] if args else "booking"))
