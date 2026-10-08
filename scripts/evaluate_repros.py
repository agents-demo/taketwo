"""Quality gate: score stored reproductions against ``tests/eval/expected.json``.

    python scripts/evaluate_repros.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taketwo.bootstrap import setup  # noqa: E402
from taketwo.domain import evaluate  # noqa: E402
from taketwo.storage import store  # noqa: E402

EXPECTED_PATH = Path(__file__).resolve().parents[1] / "tests" / "eval" / "expected.json"


def main() -> int:
    setup()
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    jobs = store.jobs()
    if not jobs:
        print("no runs to evaluate (run `taketwo record` first)")
        return 0

    failures: list[str] = []
    for job in jobs:
        repro = store.get_repro(job)
        score = evaluate.score(repro)
        print(f"{job}: verdict={score['verdict']} score={score['score']} grounded={score['grounded']}")
        if score["flags"]:
            print(f"  flags: {', '.join(score['flags'])}")

    for item in expected.get("jobs", []):
        job = item["job"]
        if job not in jobs:
            continue
        score = evaluate.score(store.get_repro(job))
        if "min_score" in item and score["score"] < item["min_score"]:
            failures.append(f"{job}: score {score['score']} < {item['min_score']}")
        if "verdict" in item and score["verdict"] != item["verdict"]:
            failures.append(f"{job}: verdict {score['verdict']} != {item['verdict']}")

    if failures:
        print("\nFAIL:\n" + "\n".join(failures))
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
