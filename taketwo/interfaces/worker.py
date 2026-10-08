"""Standalone reproduction worker (run in its own process).

Launched by the Streamlit app (or the sandbox runner) so the run has a clean
``__main__``. Progress is streamed to a JSON file the UI polls.

    python -m taketwo.interfaces.worker <video> --progress <path> [--repo ... --app ... --agentic]
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import traceback
from pathlib import Path

from taketwo.analysis.progress import Progress
from taketwo.bootstrap import run as run_async
from taketwo.bootstrap import setup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taketwo-worker")
    parser.add_argument("video")
    parser.add_argument("--progress", required=True, help="path to write progress JSON to")
    parser.add_argument("--repo", default="")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--app", default="")
    parser.add_argument("--agentic", action="store_true")
    args = parser.parse_args(argv)

    setup()
    prog = Progress()
    progress_path = Path(args.progress)
    stop = threading.Event()

    def reporter() -> None:
        while not stop.is_set():
            try:
                progress_path.write_text(json.dumps(prog.snapshot()), encoding="utf-8")
            except Exception:
                pass
            time.sleep(0.4)

    threading.Thread(target=reporter, daemon=True).start()

    from taketwo.analysis import pipeline

    strategy = pipeline.resolve(args.agentic)

    try:
        run_async(
            strategy.analyze(
                pipeline.Params(
                    video_path=args.video,
                    repo=args.repo,
                    base_branch=args.branch,
                    app_url=args.app,
                    progress=prog,
                )
            )
        )
        prog.finish(Path(args.video).stem)
    except Exception as exc:  # noqa: BLE001
        prog.fail(f"{exc}\n\n{traceback.format_exc()}")
    finally:
        stop.set()
        try:
            progress_path.write_text(json.dumps(prog.snapshot()), encoding="utf-8")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
