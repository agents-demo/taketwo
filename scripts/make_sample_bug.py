"""Create a synthetic bug submission so the demo runs without a real recording.

Writes, under ``runtime/data``:
  - ``sample_bug.mov``               the "recording" (a placeholder clip)
  - ``sample_bug.mov.timeline.json`` the inferred steps (the deterministic observe path)
  - ``sample_bug.mov.repro.json``    the reproduced run + evidence + before clip
  - ``sample_bug_proposed.patch``    the fix the sandbox would produce
  - ``sample_bug_proposed.test``     the regression test

    python scripts/make_sample_bug.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taketwo.bootstrap import setup  # noqa: E402
from taketwo.storage import runtime  # noqa: E402

STEM = "sample_bug"

TIMELINE = {
    "steps": [
        {"action": "click", "target": "text=Pick a date", "timestamp": 1.2, "confidence": 0.8},
        {"action": "click", "target": "button=15", "timestamp": 2.4, "confidence": 0.7},
        {"action": "wait", "timestamp": 3.0, "confidence": 0.5},
    ],
    "failure": {"summary": "date picker closes without selecting", "timestamp": 3.0, "signal": "blur"},
}

# A live variant: same steps, but NO repro sidecar, so the pipeline reproduces it in a
# real browser against examples/sample_app (served locally).
LIVE_TIMELINE = {
    "steps": [
        {"action": "click", "target": "#dateField", "timestamp": 1.2, "confidence": 0.9},
        {"action": "click", "target": "button.day", "timestamp": 2.4, "confidence": 0.9},
    ],
    "failure": {"summary": "", "timestamp": 0.0, "signal": ""},
}

REPRO = {
    "steps": TIMELINE["steps"],
    "evidence": {
        "console": ["pageerror: TypeError: Cannot read properties of null (reading 'value')"],
        "network": [],
        "dom": "input#date has no value",
        "summary": "TypeError: Cannot read properties of null (reading 'value')",
    },
    "verdict": "reproduced",
    "before_clip": str(runtime.ARTIFACTS_DIR / STEM / "before.png"),
}

PATCH = """--- a/src/datepicker.js
+++ b/src/datepicker.js
@@ -12,7 +12,7 @@ function onSelect(date) {
-  const value = input.value;
+  const value = input?.value ?? '';
   commit(value);
 }
"""

TEST = """def test_datepicker_select():
    # selecting a date must not throw and must set a value
    assert select_date("2026-01-15").value == "2026-01-15"
"""


def _write_clips(job: str) -> None:
    """Write placeholder before/after frames so the proof video can be built offline."""
    try:
        from PIL import Image, ImageDraw

        out = runtime.ARTIFACTS_DIR / job
        out.mkdir(parents=True, exist_ok=True)
        for name, color, text in (("before.png", (40, 20, 20), "picker closes"), ("after.png", (20, 40, 20), "date set")):
            image = Image.new("RGB", (480, 320), color)
            ImageDraw.Draw(image).text((20, 20), text, fill=(230, 230, 230))
            image.save(out / name)
    except Exception:
        pass


def main() -> int:
    setup()
    data = runtime.DATA_DIR
    (data / f"{STEM}.mov").write_bytes(b"synthetic-recording-placeholder")
    (data / f"{STEM}.mov.timeline.json").write_text(json.dumps(TIMELINE, indent=2), encoding="utf-8")
    (data / f"{STEM}.mov.repro.json").write_text(json.dumps(REPRO, indent=2), encoding="utf-8")
    (data / f"{STEM}_proposed.patch").write_text(PATCH, encoding="utf-8")
    (data / f"{STEM}_proposed.test").write_text(TEST, encoding="utf-8")
    # An explicit (offline) verification result: scenario fixed, tests pass.
    (data / f"{STEM}_proposed.result.json").write_text(
        json.dumps({"reproduced": False, "tests_pass": True}, indent=2), encoding="utf-8"
    )
    # The live fixture: a timeline but no repro sidecar -> reproduces in a real browser.
    (data / f"{STEM}_live.mov").write_bytes(b"synthetic-recording-placeholder")
    (data / f"{STEM}_live.mov.timeline.json").write_text(json.dumps(LIVE_TIMELINE, indent=2), encoding="utf-8")
    _write_clips(STEM)
    print(f"wrote synthetic submission under {data}")
    print("run: taketwo record runtime/data/sample_bug.mov")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
