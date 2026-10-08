"""Prompt for grounding an inferred step on a real element in the live page."""

REPRODUCE_AGENT_SYSTEM = """You are TakeTwo's reproduction pass. Given an ordered list of inferred steps
and the accessibility tree of the running app, map each step to a concrete selector.

Return STRICT JSON only:
{"steps": [{"action": "...", "target": "<selector or role=name>", "value": "...", "confidence": 0.0}]}
Use accessible roles/names where possible. If a step cannot be grounded, omit it."""


def build_user(timeline: dict, outline: str) -> str:
    """The per-run user message: the inferred steps plus the live page outline."""
    import json

    steps = timeline.get("steps", [])
    return (
        "Inferred steps:\n"
        + json.dumps(steps, ensure_ascii=False, indent=2)
        + "\n\nPage accessibility outline:\n"
        + (outline or "(empty)")
    )
