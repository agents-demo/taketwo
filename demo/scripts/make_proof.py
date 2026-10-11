"""Build a scenario's before/after proof from real browser frames.

Serves the buggy app and a patched copy (the scenario's ``proof`` fix), screenshots each,
and stitches a proof image + video into ``runtime/artifacts/<scenario>/``.

    python demo/scripts/make_proof.py [scenario]           # default: booking
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _scenario import app_dir, load  # noqa: E402

from scripts._harness import free_port, playwright_available, run_steps, serve  # noqa: E402
from taketwo.core.stages.prove import stitch  # noqa: E402
from taketwo.integrations import appserver  # noqa: E402
from taketwo.integrations.storage import runtime  # noqa: E402


def _capture(url: str, steps: list[dict], out: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 560, "height": 460}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        run_steps(page, steps)
        page.wait_for_timeout(500)
        page.screenshot(path=str(out))
        browser.close()


def main(name: str = "booking") -> int:
    from taketwo.core.bootstrap import setup

    setup()
    if not playwright_available():
        print("Playwright not installed.  python -m playwright install chromium")
        return 2

    root = Path(__file__).resolve().parents[2]
    scenario = load(name)
    steps, fix = scenario["steps"], scenario["proof"]

    out_dir = runtime.ARTIFACTS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)

    fixed = Path(tempfile.mkdtemp(prefix=f"taketwo_proof_{name}_")) / "fixed"
    shutil.copytree(app_dir(name), fixed)
    html = (fixed / "index.html").read_text(encoding="utf-8")
    (fixed / "index.html").write_text(html.replace(fix["find"], fix["replace"]), encoding="utf-8")

    buggy_app = serve(app_dir(name), free_port(), root)
    fixed_app = serve(fixed, free_port(), root)
    before, after = out_dir / "before.png", out_dir / "after.png"
    try:
        if not buggy_app or not fixed_app:
            print("could not start the demo app")
            return 1
        _capture(buggy_app.url, steps, before)
        _capture(fixed_app.url, steps, after)
    finally:
        appserver.stop(buggy_app)
        appserver.stop(fixed_app)

    print(f"proof: {stitch.proof(str(before), str(after), str(out_dir / 'proof.png'))}")
    print(f"video: {stitch.proof_video(str(before), str(after), str(out_dir / 'proof.mp4'))}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(main(args[0] if args else "booking"))
