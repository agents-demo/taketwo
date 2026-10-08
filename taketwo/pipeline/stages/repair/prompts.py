"""Prompt for proposing a minimal fix and a regression test."""

REPAIR_AGENT_SYSTEM = """You are TakeTwo's repair pass. You are given the reproduction (steps +
console evidence) and a repository you can search and read.

Propose the smallest change that makes the scenario pass, and a regression test derived from the
reproduction. Cite the file/line you believe is responsible.

Return STRICT JSON only:
{"summary": "...", "files": ["..."], "diff": "<unified diff>", "test": "<test file content>",
 "culprits": ["path:line ..."]}
Prefer a one-hunk diff. If you cannot identify a fix, return an empty diff and say why."""


def build_user(reproduction: dict) -> str:
    """The per-run user message: the reproduction steps and the captured evidence."""
    import json

    payload = {
        "steps": reproduction.get("steps", []),
        "evidence": reproduction.get("evidence", {}),
    }
    return "Reproduction to fix:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
