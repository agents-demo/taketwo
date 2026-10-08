"""Synthesize a short recording of the buggy interaction (for the vision path).

Serves ``examples/sample_app`` and captures staged screenshots with Playwright, then writes
them to an mp4 with **no timeline sidecar** — so ``understand`` has to sample frames and
call the vision model.

    python scripts/make_sample_clip.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _harness import free_port, playwright_available, serve  # noqa: E402

from taketwo.bootstrap import setup  # noqa: E402
from taketwo.pipeline import appserver  # noqa: E402
from taketwo.storage import runtime  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "sample_app"


def _frames(url: str) -> list:
    from PIL import Image
    from playwright.sync_api import sync_playwright

    shots = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 520, "height": 430}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(500)
        shots.append(page.screenshot())
        page.hover("#dateField")
        page.wait_for_timeout(300)
        shots.append(page.screenshot())
        page.click("#dateField")  # picker opens
        page.wait_for_timeout(400)
        shots.append(page.screenshot())
        shots.append(page.screenshot())
        page.click("button.day")  # triggers the seeded TypeError
        page.wait_for_timeout(400)
        shots.append(page.screenshot())
        browser.close()
    return [Image.open(io.BytesIO(b)).convert("RGB") for b in shots]


def main() -> int:
    setup()
    if not playwright_available():
        print("Playwright not installed.  python -m playwright install chromium")
        return 2

    app = serve(APP, free_port(), ROOT)
    try:
        if not app:
            print("could not start the sample app")
            return 1
        frames = _frames(app.url)
    finally:
        appserver.stop(app)

    out = runtime.DATA_DIR / "sample_bug_clip.mp4"
    import imageio.v2 as iio
    import numpy as np

    # Hold each frame a touch so motion is visible (≈4 fps).
    reel = []
    for frame in frames:
        reel.extend([np.asarray(frame)] * 2)
    with iio.get_writer(str(out), fps=8) as writer:
        for frame in reel:
            writer.append_data(frame)

    sidecar = Path(f"{out}.timeline.json")
    if sidecar.exists():
        sidecar.unlink()  # ensure the vision path, not the sidecar shortcut
    print(f"clip: {out}  ({len(reel)} frames)")
    print(f"sidecar present: {sidecar.exists()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
