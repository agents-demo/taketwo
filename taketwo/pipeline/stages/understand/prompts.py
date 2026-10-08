"""Vision prompt for inferring the reporter's steps from sampled frames."""

VISION_AGENT_SYSTEM = """You are TakeTwo's observation pass. You are given a contact sheet of frames
from a screen recording of a bug, labelled with timestamps, plus measured motion events.

Infer the ordered steps the user took (click / type / select / navigate), grounding each step in
visible text or UI elements. Identify the moment the app misbehaved.

Return STRICT JSON only:
{
  "steps": [{"action": "...", "target": "...", "value": "...", "timestamp": 0.0, "confidence": 0.0, "evidence": "..."}],
  "failure": {"summary": "...", "timestamp": 0.0, "signal": "..."}
}
Never invent steps you cannot see. If unsure, lower the confidence."""


def build_user(contact_sheet: str | None, motion: list[dict]) -> str:
    """The per-run user message: which image to read, plus the measured motion."""
    lines = ["Infer the reporter's steps from the recording."]
    if contact_sheet:
        lines.append(f"Read the contact sheet at: {contact_sheet}")
    if motion:
        lines.append("Measured motion events (timestamp, score): " + ", ".join(f"{m['timestamp']}s/{m['score']}" for m in motion))
    else:
        lines.append("No significant motion was measured.")
    return "\n".join(lines)
