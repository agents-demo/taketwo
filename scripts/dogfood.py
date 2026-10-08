"""Live end-to-end dogfood: reproduce a real browser bug with no fixtures.

Serves ``examples/sample_app`` (buggy) and a fixed copy, drives the real Playwright
reproduce + re-run path, and writes a before/after proof image and video.

    pip install -r requirements.txt
    python -m playwright install chromium
    python scripts/dogfood.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _harness import live_reproduce, playwright_available, rerun, serve  # noqa: E402

from taketwo.bootstrap import run, setup  # noqa: E402
from taketwo.pipeline import appserver  # noqa: E402
from taketwo.pipeline.stages.prove import stitch  # noqa: E402
from taketwo.storage import runtime  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "sample_app"
BUG = "const value = input.value;"
FIX = "const value = button.textContent;"
STEPS = [
    {"action": "click", "target": "#dateField", "timestamp": 1.0, "confidence": 0.9},
    {"action": "click", "target": "button.day", "timestamp": 2.0, "confidence": 0.9},
]


async def _run(buggy_url: str, fixed_url: str, video: str) -> dict:
    job = "dogfood"
    result = await live_reproduce(buggy_url, STEPS, job, video)
    session = result["session"]
    before = result["before"]

    after, after_signal = "", None
    if fixed_url and getattr(session.browser, "live", False):
        await session.browser.navigate(fixed_url)
        after_signal = await rerun(session, STEPS)
        after = await session.browser.snapshot(runtime.ARTIFACTS_DIR / job / "after.png") or ""

    proof_dir = runtime.ARTIFACTS_DIR / job
    return {
        "live": getattr(session.browser, "live", False),
        "reproduction": result["reproduction"],
        "after_signal": after_signal,
        "proof_png": stitch.proof(before, after, str(proof_dir / "proof.png")) or "",
        "proof_mp4": stitch.proof_video(before, after, str(proof_dir / "proof.mp4")) or "",
    }


def main() -> int:
    setup()
    if not playwright_available():
        print("Playwright not installed.")
        print("  pip install -r requirements.txt && python -m playwright install chromium")
        return 2

    work = Path(tempfile.mkdtemp(prefix="taketwo_dogfood_"))
    fixed_dir = work / "fixed"
    shutil.copytree(APP, fixed_dir)
    html = (fixed_dir / "index.html").read_text(encoding="utf-8")
    (fixed_dir / "index.html").write_text(html.replace(BUG, FIX), encoding="utf-8")
    video = work / "bug.mov"
    video.write_bytes(b"")

    buggy = serve(APP, 8137, ROOT)
    fixed = serve(fixed_dir, 8138, ROOT)
    try:
        if not buggy:
            print("could not start the sample app")
            return 1
        out = run(_run(buggy.url, fixed.url if fixed else "", str(video)))
    finally:
        appserver.stop(buggy)
        appserver.stop(fixed)

    repro = out["reproduction"]
    signal = repro.get("evidence", {}).get("summary")
    print(f"live browser:        {out['live']}")
    print(f"before verdict:      {repro.get('verdict')}  (signal: {signal})")
    print(f"signal after fix:    {out['after_signal'] or '(none)'}")
    print(f"proof image:         {out['proof_png']}")
    print(f"proof video:         {out['proof_mp4']}")

    ok = bool(fixed) and repro.get("verdict") == "reproduced" and out["after_signal"] == "" and bool(out["proof_mp4"])
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
