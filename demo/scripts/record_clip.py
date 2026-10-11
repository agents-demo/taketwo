"""Record a demo scenario in a real browser and write its clip.

Drives the scenario's steps with Playwright, screenshots each one, and stitches an mp4
(no timeline sidecar), so ``understand`` has to watch the video.

    python demo/scripts/record_clip.py [scenario]          # default: booking
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _scenario import app_dir, clip, load  # noqa: E402

from scripts._harness import free_port, playwright_available, run_steps, serve  # noqa: E402


def _frames(url: str, steps: list[dict]) -> list:
    from PIL import Image
    from playwright.sync_api import sync_playwright

    shots = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 520, "height": 430}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(500)
        shots.append(page.screenshot())
        for step in steps:
            run_steps(page, [step])
            page.wait_for_timeout(350)
            shots.append(page.screenshot())
        browser.close()
    return [Image.open(io.BytesIO(b)).convert("RGB") for b in shots]


def main(name: str = "booking") -> int:
    from taketwo.core.bootstrap import setup
    from taketwo.integrations import appserver

    setup()
    if not playwright_available():
        print("Playwright not installed.  python -m playwright install chromium")
        return 2

    root = Path(__file__).resolve().parents[2]
    out = clip(name)
    app = serve(app_dir(name), free_port(), root)
    try:
        if not app:
            print("could not start the demo app")
            return 1
        frames = _frames(app.url, load(name)["steps"])
    finally:
        appserver.stop(app)

    import imageio.v2 as iio
    import numpy as np

    reel = []
    for frame in frames:
        reel.extend([np.asarray(frame)] * 2)
    with iio.get_writer(str(out), fps=8) as writer:
        for frame in reel:
            writer.append_data(frame)
    print(f"clip: {out}  ({len(reel)} frames)")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(main(args[0] if args else "booking"))
