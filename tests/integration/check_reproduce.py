"""Live end-to-end: reproduce a scenario's bug in a real browser, then prove the fix.

Serves the buggy app and a patched copy, drives the real reproduce + re-run path, and
writes a before/after proof. No fixtures, no sidecars — the browser is real.

    python tests/integration/check_reproduce.py [scenario]             # default: booking
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (scripts._harness)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))  # demos/ (_scenario)

from _scenario import app_dir, load  # noqa: E402

from scripts._harness import free_port, live_reproduce, playwright_available, rerun, serve  # noqa: E402
from taketwo.core.stages.prove import stitch  # noqa: E402
from taketwo.integrations import appserver  # noqa: E402
from taketwo.integrations.storage import runtime  # noqa: E402


async def _run(buggy_url: str, fixed_url: str, video: str, steps: list[dict], job: str) -> dict:
    result = await live_reproduce(buggy_url, steps, job, video)
    session = result["session"]
    before = result["before"]

    after, after_signal = "", None
    if fixed_url and getattr(session.browser, "live", False):
        await session.browser.navigate(fixed_url)
        after_signal = await rerun(session, steps)
        after = await session.browser.snapshot(runtime.ARTIFACTS_DIR / job / "after.png") or ""

    proof_dir = runtime.ARTIFACTS_DIR / job
    return {
        "live": getattr(session.browser, "live", False),
        "reproduction": result["reproduction"],
        "after_signal": after_signal,
        "proof_png": stitch.proof(before, after, str(proof_dir / "proof.png")) or "",
        "proof_mp4": stitch.proof_video(before, after, str(proof_dir / "proof.mp4")) or "",
    }


def main(name: str = "booking") -> int:
    from taketwo.core.bootstrap import run, setup

    setup()
    if not playwright_available():
        print("Playwright not installed.")
        print("  pip install -r requirements.txt && python -m playwright install chromium")
        return 2

    root = Path(__file__).resolve().parents[2]
    scenario = load(name)
    steps, fix = scenario["steps"], scenario["proof"]

    work = Path(tempfile.mkdtemp(prefix=f"taketwo_live_{name}_"))
    fixed = work / "fixed"
    shutil.copytree(app_dir(name), fixed)
    html = (fixed / "index.html").read_text(encoding="utf-8")
    (fixed / "index.html").write_text(html.replace(fix["find"], fix["replace"]), encoding="utf-8")
    video = work / "bug.mov"
    video.write_bytes(b"")

    buggy_app = serve(app_dir(name), free_port(), root)
    fixed_app = serve(fixed, free_port(), root)
    try:
        if not buggy_app:
            print("could not start the demo app")
            return 1
        out = run(_run(buggy_app.url, fixed_app.url if fixed_app else "", str(video), steps, name))
    finally:
        appserver.stop(buggy_app)
        appserver.stop(fixed_app)

    repro = out["reproduction"]
    signal = repro.get("evidence", {}).get("summary")
    print(f"live browser:     {out['live']}")
    print(f"before verdict:   {repro.get('verdict')}  (signal: {signal})")
    print(f"signal after fix: {out['after_signal'] or '(none)'}")
    print(f"proof image:      {out['proof_png']}")
    print(f"proof video:      {out['proof_mp4']}")

    ok = bool(fixed_app) and repro.get("verdict") == "reproduced" and out["after_signal"] == "" and bool(out["proof_mp4"])
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(main(args[0] if args else "booking"))
