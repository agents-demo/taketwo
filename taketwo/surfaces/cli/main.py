"""Command-line interface for taketwo: argument parsing and dispatch.

Usage:
    python -m taketwo.surfaces.cli record [video]
    python -m taketwo.surfaces.cli history
    python -m taketwo.surfaces.cli show [job]
    python -m taketwo.surfaces.cli reset
"""

from __future__ import annotations

import argparse
import sys

from taketwo.core.bootstrap import setup
from taketwo.integrations.storage import runtime
from taketwo.surfaces.cli.commands import history, record, reset, show


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    setup()
    _configure_console()

    parser = argparse.ArgumentParser(prog="taketwo", description="TakeTwo CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="reproduce and fix a bug from a recording")
    p_record.add_argument(
        "video",
        nargs="?",
        default=str(runtime.PROJECT_ROOT / "demos" / "scenarios" / "booking" / "clip.mp4"),
        help="recording path",
    )
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
        return record.run(args.video, args.repo, args.branch, args.app, args.agentic)
    if args.command == "history":
        return history.run()
    if args.command == "show":
        return show.run(args.job)
    if args.command == "reset":
        return reset.run()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
