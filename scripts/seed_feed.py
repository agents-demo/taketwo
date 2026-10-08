"""Seed the feed with a handful of runs so the deck is swipeable (demo/dev).

Runs the deterministic pipeline several times over copies of the sample fixtures, with a
mix of verdicts: odd clips are 'fixed' (sidecar + verification result), even clips are
left 'unclear' (timeline only) so the feed shows both states.

    python scripts/seed_feed.py [count]
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from taketwo import pipeline  # noqa: E402
from taketwo.bootstrap import run, setup  # noqa: E402
from taketwo.storage import runtime  # noqa: E402

BASE = "sample_bug"


def _ensure_base() -> Path:
    data = runtime.DATA_DIR
    if not (data / f"{BASE}.mov").exists():
        import make_sample_bug

        make_sample_bug.main()
    return data


def main(count: int = 5) -> int:
    setup()
    data = _ensure_base()
    made = 0
    for i in range(1, count + 1):
        stem = BASE if i == 1 else f"{BASE}_{i}"
        video = data / f"{stem}.mov"
        shutil.copyfile(data / f"{BASE}.mov", video)
        shutil.copyfile(data / f"{BASE}.mov.timeline.json", data / f"{stem}.mov.timeline.json")

        fixed = i % 2 == 1
        if fixed:
            shutil.copyfile(data / f"{BASE}.mov.repro.json", data / f"{stem}.mov.repro.json")
            for suffix in (".patch", ".test", ".result.json"):
                shutil.copyfile(data / f"{BASE}_proposed{suffix}", data / f"{stem}_proposed{suffix}")

        try:
            run(pipeline.resolve().analyze(pipeline.Params(video_path=str(video))))
            made += 1
            print(f"seeded {stem}: {'fixed' if fixed else 'unclear'}")
        except Exception as exc:  # noqa: BLE001
            print(f"skip {stem}: {exc}")
    print(f"\n{made} runs seeded; open the feed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 5))
