"""Reproduction-success benchmark over seeded browser bugs in two different apps.

Serves seeded pages (a date picker and a login form), drives the real reproduce path in a
live browser using **label-based** steps (exercising the selector fallback ladder), and
reports the reproduce rate — the "does it generalize" number to watch.

    python scripts/benchmark.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _harness import live_reproduce, playwright_available, serve  # noqa: E402

from taketwo.bootstrap import run, setup  # noqa: E402
from taketwo.pipeline import appserver  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

PICKER = """<!doctype html>
<html><body>
  <div id="dateField" role="textbox" aria-label="Pick a date" tabindex="0">Pick a date</div>
  <div id="picker" hidden><button class="day">15</button></div>
  <script>
    const field = document.getElementById('dateField');
    const picker = document.getElementById('picker');
    field.addEventListener('click', () => { picker.hidden = false; });
    document.querySelector('.day').addEventListener('click', () => {
      /*BUG*/
      field.textContent = '15';
      picker.hidden = true;
    });
  </script>
</body></html>
"""

FORM = """<!doctype html>
<html><body>
  <form id="login">
    <input id="user" aria-label="Username" />
    <button id="go">Sign in</button>
  </form>
  <script>
    document.getElementById('go').addEventListener('click', (event) => {
      event.preventDefault();
      /*BUG*/
      document.getElementById('user').value = 'ok';
    });
  </script>
</body></html>
"""

STEPS_PICKER = [
    {"action": "click", "target": "Pick a date", "timestamp": 1.0, "confidence": 0.9},
    {"action": "click", "target": "15", "timestamp": 2.0, "confidence": 0.9},
]
STEPS_FORM = [{"action": "click", "target": "Sign in", "timestamp": 1.0, "confidence": 0.9}]

CASES = [
    ("picker_throw", PICKER, STEPS_PICKER, "throw new Error('boom on select');", True),
    ("picker_null", PICKER, STEPS_PICKER, "const value = null.value;", True),
    ("picker_control", PICKER, STEPS_PICKER, "", False),
    ("form_throw", FORM, STEPS_FORM, "throw new Error('bad login');", True),
    ("form_reference", FORM, STEPS_FORM, "missingFn();", True),
    ("form_control", FORM, STEPS_FORM, "", False),
]


async def _one(url: str, steps: list[dict], job: str, video: str) -> str:
    result = await live_reproduce(url, steps, job, video)
    return result["reproduction"].get("verdict", "unclear")


def main() -> int:
    setup()
    if not playwright_available():
        print("Playwright not installed.")
        print("  pip install -r requirements.txt && python -m playwright install chromium")
        return 2

    work = Path(tempfile.mkdtemp(prefix="taketwo_bench_"))
    video = work / "bug.mov"
    video.write_bytes(b"")

    correct, live_seen = 0, False
    print(f"{'case':<18} {'verdict':<16} {'expected':<10} result")
    for index, (name, template, steps, bug, expected_reproduced) in enumerate(CASES):
        case_dir = work / name
        case_dir.mkdir()
        (case_dir / "index.html").write_text(template.replace("/*BUG*/", bug), encoding="utf-8")
        app = serve(case_dir, 8140 + index, ROOT)
        try:
            if not app:
                print(f"{name:<18} {'(no app)':<16} {'-':<10} FAIL")
                continue
            verdict = run(_one(app.url, steps, f"bench_{name}", str(video)))
        finally:
            appserver.stop(app)
        live_seen = live_seen or verdict in ("reproduced", "not_reproduced")
        matched = (verdict == "reproduced") == expected_reproduced
        correct += int(matched)
        print(f"{name:<18} {verdict:<16} {str(expected_reproduced):<10} {'ok' if matched else 'FAIL'}")

    total = len(CASES)
    rate = correct / total
    print(f"\nreproduce rate: {correct}/{total} = {rate:.0%}")
    ok = live_seen and rate >= 0.75
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
