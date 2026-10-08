"""Seed two fully *reproduced* scenarios (with real before/after proof).

Each scenario has its own buggy app, so the feed shows genuine "Fixed" runs with a
before/after video — no model calls needed (deterministic fixtures).

    python scripts/seed_reproduced.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _harness import free_port, playwright_available, serve  # noqa: E402

from taketwo import pipeline  # noqa: E402
from taketwo.bootstrap import run, setup  # noqa: E402
from taketwo.pipeline import appserver  # noqa: E402
from taketwo.pipeline.stages.prove import stitch  # noqa: E402
from taketwo.storage import runtime  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

SCENARIOS = [
    {
        "stem": "repro_date",
        "app": ROOT / "examples" / "sample_app",
        "bug": "const value = input.value;",
        "fix": "const value = button.textContent;",
        "clicks": ["#dateField", "button.day"],
        "steps": [
            {"action": "click", "target": "#dateField", "timestamp": 1.0, "confidence": 0.9},
            {"action": "click", "target": "button.day", "timestamp": 2.0, "confidence": 0.9},
        ],
        "evidence": "TypeError: Cannot read properties of null (reading 'value')",
        "patch": "--- a/src/datepicker.js\n+++ b/src/datepicker.js\n@@\n-  const value = input.value;\n+  const value = input?.value ?? '';\n",
    },
    {
        "stem": "repro_login",
        "app": ROOT / "examples" / "sample_form",
        "bug": "const email = field.value;",
        "fix": "const email = document.getElementById('user').value;",
        "clicks": ["#go"],
        "steps": [{"action": "click", "target": "#go", "timestamp": 1.0, "confidence": 0.9}],
        "evidence": "TypeError: Cannot read properties of null (reading 'value')",
        "patch": "--- a/src/login.js\n+++ b/src/login.js\n@@\n-  const email = field.value;\n+  const email = document.getElementById('user').value;\n",
    },
]


def _capture(url: str, clicks: list[str], out: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 560, "height": 470}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        for selector in clicks:
            try:
                page.click(selector)
            except Exception:
                pass
            page.wait_for_timeout(250)
        page.wait_for_timeout(350)
        page.screenshot(path=str(out))
        browser.close()


def _seed(scenario: dict) -> None:
    stem = scenario["stem"]
    data = runtime.DATA_DIR
    out_dir = runtime.ARTIFACTS_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    video = data / f"{stem}.mov"
    video.write_bytes(b"synthetic-recording-placeholder")
    (data / f"{stem}.mov.timeline.json").write_text(
        json.dumps({"steps": scenario["steps"], "failure": {}}, indent=2), encoding="utf-8"
    )
    (data / f"{stem}.mov.repro.json").write_text(
        json.dumps(
            {
                "steps": scenario["steps"],
                "evidence": {"console": [scenario["evidence"]], "network": [], "dom": "", "summary": scenario["evidence"]},
                "verdict": "reproduced",
                "before_clip": str(out_dir / "before.png"),
                "question": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (data / f"{stem}_proposed.patch").write_text(scenario["patch"], encoding="utf-8")
    (data / f"{stem}_proposed.test").write_text(
        "def test_regression():\n    # the scenario no longer throws\n    assert select() == 'ok'\n", encoding="utf-8"
    )
    (data / f"{stem}_proposed.result.json").write_text(
        json.dumps({"reproduced": False, "tests_pass": True}, indent=2), encoding="utf-8"
    )

    fixed_dir = Path(tempfile.mkdtemp(prefix=f"taketwo_{stem}_")) / "fixed"
    shutil.copytree(scenario["app"], fixed_dir)
    html = (fixed_dir / "index.html").read_text(encoding="utf-8")
    (fixed_dir / "index.html").write_text(html.replace(scenario["bug"], scenario["fix"]), encoding="utf-8")

    buggy = serve(scenario["app"], free_port(), ROOT)
    fixed = serve(fixed_dir, free_port(), ROOT)
    try:
        if buggy:
            _capture(buggy.url, scenario["clicks"], out_dir / "before.png")
        if fixed:
            _capture(fixed.url, scenario["clicks"], out_dir / "after.png")
    finally:
        appserver.stop(buggy)
        appserver.stop(fixed)

    stitch.proof(str(out_dir / "before.png"), str(out_dir / "after.png"), str(out_dir / "proof.png"))
    stitch.proof_video(str(out_dir / "before.png"), str(out_dir / "after.png"), str(out_dir / "proof.mp4"))

    outcome = run(pipeline.resolve().analyze(pipeline.Params(video_path=str(video))))
    print(f"{stem}: verdict={outcome['reproduction'].get('verdict')} proof={bool((outcome.get('proof') or {}).get('proof_video'))}")


def main() -> int:
    setup()
    if not playwright_available():
        print("Playwright not installed.  python -m playwright install chromium")
        return 2
    for scenario in SCENARIOS:
        _seed(scenario)
    print("\nseeded reproduced scenarios; open the feed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
