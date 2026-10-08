"""Command-line interface for taketwo.

Usage:
    python -m taketwo.interfaces.cli record [video]
    python -m taketwo.interfaces.cli history
    python -m taketwo.interfaces.cli show [job]
    python -m taketwo.interfaces.cli reset
"""

from __future__ import annotations

import argparse
import sys

from taketwo.backend import ConfigError
from taketwo.bootstrap import run as run_async
from taketwo.bootstrap import setup
from taketwo.domain import render
from taketwo.storage import runtime, store

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _print_reproduction(repro: dict) -> None:
    if not repro:
        return
    print(f"\nReproduction · {repro.get('verdict', 'unclear')}")
    steps = repro.get("steps") or []
    for step in steps[:10]:
        target = step.get("target") or "?"
        print(f"  {step.get('index', 0) + 1}. {step.get('action')} {target}")
    signal = repro.get("evidence", {}).get("summary")
    if signal:
        print(f"  signal: {signal}")
    if repro.get("question"):
        print(f"  question: {repro['question']}")


def cmd_record(video: str, repo: str, base_branch: str, app_url: str, agentic: bool) -> int:
    from taketwo.analysis import pipeline

    strategy = pipeline.resolve(agentic)
    try:
        outcome = run_async(
            strategy.analyze(
                pipeline.Params(video_path=video, repo=repo, base_branch=base_branch, app_url=app_url)
            )
        )
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}")
        return 2

    print(f"\n[taketwo] {str(outcome.get('result') or '').strip()}")
    _print_reproduction(outcome.get("reproduction") or {})
    fix = outcome.get("fix") or {}
    if fix.get("summary"):
        print(f"\nFix: {fix['summary']}")
    proof = outcome.get("proof") or {}
    if proof.get("proof_path"):
        print(f"Proof: {proof['proof_path']}")
    if outcome.get("summary_path"):
        print(f"summary saved to: {outcome['summary_path']}")
    return 0


def cmd_history() -> int:
    found = store.jobs()
    if not found:
        print("No runs yet. Run `record`.")
        return 0
    print(f"Runs ({len(found)}):\n")
    for job in found[:10]:
        repro = store.get_repro(job)
        print(f"  {job} · {repro.get('verdict', '?')} · {repro.get('evidence', {}).get('summary', '')}")
    return 0


def cmd_show(job: str | None) -> int:
    selected = job or store.latest()
    if not selected:
        print("No runs yet.")
        return 0
    repro = store.get_repro(selected) or {}
    print(render.issue_markdown({"repo": selected}, repro))
    return 0


def cmd_reset() -> int:
    store.reset()
    print("Cleared saved runs.")
    return 0


def main(argv: list[str] | None = None) -> int:
    setup()
    parser = argparse.ArgumentParser(prog="taketwo", description="TakeTwo CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="reproduce and fix a bug from a recording")
    p_record.add_argument("video", nargs="?", default=str(runtime.DATA_DIR / "sample_bug.mov"), help="recording path")
    p_record.add_argument("--repo", default="", help="repository as owner/name")
    p_record.add_argument("--branch", default="main", help="base branch")
    p_record.add_argument("--app", default="", help="URL of the running app")
    p_record.add_argument("--agentic", action="store_true", help="let the model drive the run")

    sub.add_parser("history", help="show recent runs")
    p_show = sub.add_parser("show", help="show a run's issue")
    p_show.add_argument("job", nargs="?", default=None, help="job id")
    sub.add_parser("reset", help="clear saved runs")

    args = parser.parse_args(argv)

    if args.command == "record":
        return cmd_record(args.video, args.repo, args.branch, args.app, args.agentic)
    if args.command == "history":
        return cmd_history()
    if args.command == "show":
        return cmd_show(args.job)
    if args.command == "reset":
        return cmd_reset()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
