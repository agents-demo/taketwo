"""Build a *real* sample proof — actual browser screenshots of the bug, before and after.

Serves ``examples/sample_app`` (buggy) and a fixed copy, drives them with Playwright,
captures the state after selecting a date, and stitches a before/after proof image + video
into the sample's artifacts (replacing the flat placeholders).

    python scripts/make_sample_video.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _harness import free_port, playwright_available, serve  # noqa: E402

from taketwo.bootstrap import setup  # noqa: E402
from taketwo.pipeline import appserver  # noqa: E402
from taketwo.pipeline.stages.prove import stitch  # noqa: E402
from taketwo.storage import runtime  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "sample_app"
BUG = "const value = input.value;"
FIX = "const value = button.textContent;"
STEM = "sample_bug"


def _capture(url: str, out: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 560, "height": 460}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        page.click("#dateField")
        page.click("button.day")  # first day
        page.wait_for_timeout(500)
        page.screenshot(path=str(out))
        browser.close()


def main() -> int:
    setup()
    if not playwright_available():
        print("Playwright not installed.  pip install -r requirements.txt && python -m playwright install chromium")
        return 2

    data = runtime.DATA_DIR
    if not (data / f"{STEM}.mov").exists():
        import make_sample_bug

        make_sample_bug.main()

    out_dir = runtime.ARTIFACTS_DIR / STEM
    out_dir.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix="taketwo_video_"))
    fixed_dir = work / "fixed"
    shutil.copytree(APP, fixed_dir)
    html = (fixed_dir / "index.html").read_text(encoding="utf-8")
    (fixed_dir / "index.html").write_text(html.replace(BUG, FIX), encoding="utf-8")

    buggy = serve(APP, free_port(), ROOT)
    fixed = serve(fixed_dir, free_port(), ROOT)
    before, after = out_dir / "before.png", out_dir / "after.png"
    try:
        if not buggy or not fixed:
            print("could not start the sample app")
            return 1
        _capture(buggy.url, before)
        _capture(fixed.url, after)
    finally:
        appserver.stop(buggy)
        appserver.stop(fixed)

    proof_png = stitch.proof(str(before), str(after), str(out_dir / "proof.png"))
    proof_mp4 = stitch.proof_video(str(before), str(after), str(out_dir / "proof.mp4"))
    print(f"before: {before}")
    print(f"after:  {after}")
    print(f"proof:  {proof_png}")
    print(f"video:  {proof_mp4}")
    print("\nThe sample's proof now shows real browser frames.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
