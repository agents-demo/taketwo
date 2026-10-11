"""``record`` — reproduce and fix a bug from a recording."""

from __future__ import annotations

from taketwo.backend import ConfigError
from taketwo.bootstrap import run as run_async


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


def run(video: str, repo: str, base_branch: str, app_url: str, agentic: bool) -> int:
    from taketwo import pipeline

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
