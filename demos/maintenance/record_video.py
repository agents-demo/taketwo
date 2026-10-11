"""Record a demo scenario as a real ~5 s video clip.

Uses Playwright's built-in recorder: it drives the scenario's steps in a real browser
*while recording*, then transcodes the recording to ``scenarios/<name>/clip.mp4`` (no
timeline sidecar, so ``understand`` has to watch the video).

    python demos/maintenance/record_video.py [scenario]          # default: booking
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (scripts._harness)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # demos/ (for _scenario)

from _scenario import app_dir, clip, load  # noqa: E402

from scripts._harness import free_port, playwright_available, run_steps, serve  # noqa: E402

INTRO_MS = 800  # hold on the initial page
PACE_MS = 1200  # pause after each step
OUTRO_MS = 800  # hold at the end


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
            run_steps(page, [step])
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
    if not playwright_available():
        print("Playwright not installed.  python -m playwright install chromium")
        return 2

    root = Path(__file__).resolve().parents[2]
    out = clip(name)
    work = Path(tempfile.mkdtemp(prefix=f"taketwo_rec_{name}_"))
    app = serve(app_dir(name), free_port(), root)
    try:
        if not app:
            print("could not start the demo app")
            return 1
        webm = _record(app.url, load(name)["steps"], work)
    finally:
        appserver.stop(app)

    frames = _to_mp4(webm, out)
    shutil.rmtree(work, ignore_errors=True)
    print(f"clip: {out}  ({frames} frames)")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(main(args[0] if args else "booking"))
