"""Pure text rendering of a reproduction's issue and PR.

Markdown only, no I/O. ``job_id`` is re-exported from :mod:`taketwo.domain.submission`.
"""

from __future__ import annotations

from typing import Any

from taketwo.domain.submission import job_id  # noqa: F401  (re-exported)

__all__ = ["issue_markdown", "pr_markdown", "steps_table", "job_id"]


def steps_table(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return "_No steps were inferred._"
    rows = ["| # | action | target | value | t (s) | conf |", "|---|---|---|---|---|---|"]
    for step in steps:
        rows.append(
            f"| {step.get('index', 0) + 1} | {step.get('action', '')} | {step.get('target', '')} "
            f"| {step.get('value', '')} | {step.get('timestamp', 0.0):.2f} | {step.get('confidence', 0.0):.2f} |"
        )
    return "\n".join(rows)


def _evidence_block(evidence: dict[str, Any]) -> str:
    console = "\n".join(f"    {line}" for line in evidence.get("console", [])) or "    (none)"
    network = "\n".join(f"    {line}" for line in evidence.get("network", [])) or "    (none)"
    return (
        "**Failure signal**\n\n"
        f"- Summary: {evidence.get('summary') or '(none)'}\n"
        f"- DOM: {evidence.get('dom') or '(none)'}\n\n"
        "Console:\n```\n" + console + "\n```\n\n"
        "Network:\n```\n" + network + "\n```"
    )


def issue_markdown(submission: dict[str, Any], reproduction: dict[str, Any]) -> str:
    verdict = reproduction.get("verdict", "unclear")
    header = f"# Reproduced: {submission.get('repo') or submission.get('video_path')}"
    return "\n".join(
        [
            header,
            "",
            f"Status: **{verdict}**",
            "",
            "## Steps to reproduce",
            "",
            steps_table(reproduction.get("steps", [])),
            "",
            "## Evidence",
            "",
            _evidence_block(reproduction.get("evidence", {})),
            "",
            f"Before clip: `{reproduction.get('before_clip') or '(none)'}`",
            "",
        ]
    )


def pr_markdown(
    submission: dict[str, Any],
    reproduction: dict[str, Any],
    fix: dict[str, Any],
    proof: dict[str, Any],
) -> str:
    culprits = "\n".join(f"- {c}" for c in fix.get("culprits", [])) or "- (none identified)"
    files = "\n".join(f"- `{f}`" for f in fix.get("files", [])) or "- (none)"
    return "\n".join(
        [
            f"# Fix: {fix.get('summary') or 'resolve the reproduced bug'}",
            "",
            f"Reproduced from `{reproduction.get('before_clip') or submission.get('video_path')}`.",
            "",
            "## Change",
            "",
            fix.get("diff", "") or "(no diff)",
            "",
            "## Files",
            "",
            files,
            "",
            "## Suspected cause",
            "",
            culprits,
            "",
            "## Regression test",
            "",
            "```\n" + (fix.get("test", "") or "(none)") + "\n```",
            "",
            "## Proof",
            "",
            f"Before/after video: `{proof.get('proof_path') or '(pending)'}`",
            "",
        ]
    )
