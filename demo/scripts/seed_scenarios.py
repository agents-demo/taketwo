"""Seed reproduced demo runs (one per scenario) so the feed and scoreboard have content.

No model calls: it writes the deterministic fixtures for each scenario (timeline + repro
sidecars), captures real before/after frames, and runs the offline pipeline.

    python demo/scripts/seed_scenarios.py [scenario ...]   # default: all
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _scenario import app_dir, load, names  # noqa: E402

from scripts._harness import free_port, playwright_available, run_steps, serve  # noqa: E402
from taketwo.core.stages.prove import stitch  # noqa: E402
from taketwo.integrations import appserver  # noqa: E402
from taketwo.integrations.storage import runtime  # noqa: E402


def _capture(url: str, steps: list[dict], out: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 560, "height": 470}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        run_steps(page, steps)
        page.wait_for_timeout(350)
        page.screenshot(path=str(out))
        browser.close()


def _seed(name: str) -> None:
    from taketwo import core
    from taketwo.core.bootstrap import run

    root = Path(__file__).resolve().parents[2]
    scenario = load(name)
    steps, fix = scenario["steps"], scenario["proof"]
    evidence = scenario["evidence"]

    data = runtime.DATA_DIR
    out_dir = runtime.ARTIFACTS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)

    video = data / f"{name}.mov"
    video.write_bytes(b"synthetic-recording-placeholder")
    (data / f"{name}.mov.timeline.json").write_text(
        json.dumps({"steps": steps, "failure": {}}, indent=2), encoding="utf-8"
    )
    (data / f"{name}.mov.repro.json").write_text(
        json.dumps(
            {
                "steps": steps,
                "evidence": {"console": [evidence], "network": [], "dom": "", "summary": evidence},
                "verdict": "reproduced",
                "before_clip": str(out_dir / "before.png"),
                "question": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (data / f"{name}_proposed.patch").write_text(scenario.get("patch", ""), encoding="utf-8")
    (data / f"{name}_proposed.test").write_text(
        "def test_regression():\n    # the scenario no longer throws\n    assert select() == 'ok'\n", encoding="utf-8"
    )
    (data / f"{name}_proposed.result.json").write_text(
        json.dumps({"reproduced": False, "tests_pass": True}, indent=2), encoding="utf-8"
    )

    fixed = Path(tempfile.mkdtemp(prefix=f"taketwo_{name}_")) / "fixed"
    shutil.copytree(app_dir(name), fixed)
    html = (fixed / "index.html").read_text(encoding="utf-8")
    (fixed / "index.html").write_text(html.replace(fix["find"], fix["replace"]), encoding="utf-8")

    buggy_app = serve(app_dir(name), free_port(), root)
    fixed_app = serve(fixed, free_port(), root)
    try:
        if buggy_app:
            _capture(buggy_app.url, steps, out_dir / "before.png")
        if fixed_app:
            _capture(fixed_app.url, steps, out_dir / "after.png")
    finally:
        appserver.stop(buggy_app)
        appserver.stop(fixed_app)

    stitch.proof(str(out_dir / "before.png"), str(out_dir / "after.png"), str(out_dir / "proof.png"))
    stitch.proof_video(str(out_dir / "before.png"), str(out_dir / "after.png"), str(out_dir / "proof.mp4"))

    outcome = run(core.resolve().analyze(core.Params(video_path=str(video))))
    verdict = outcome["reproduction"].get("verdict")
    proof = bool((outcome.get("proof") or {}).get("proof_video"))
    print(f"{name}: verdict={verdict} proof={proof}")


def main(argv: list[str] | None = None) -> int:
    from taketwo.core.bootstrap import setup

    setup()
    if not playwright_available():
        print("Playwright not installed.  python -m playwright install chromium")
        return 2
    for name in argv or names():
        _seed(name)
    print("\nseeded reproduced scenarios; open the feed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or None))
