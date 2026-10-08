"""Reading an agent's reply: run it, extract the text, parse the strict JSON it returns.

Shared by the stages that reason with a model (``understand``, ``repair``); keeping
the run + parse here means a stage only decides *what* to ask, not *how* to reach it.
The only pipeline module besides ``stages/*/build_agent`` allowed to touch the
backend, and it does so through the backend façade.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any


async def ask(agent: Any, user_prompt: str, *, attempts: int | None = None) -> str:
    """Run ``agent`` on ``user_prompt`` and return its text output.

    Retries transient failures with exponential backoff (``LLM_RETRIES`` + 1 tries).
    """
    from taketwo.backend import run_agent
    from taketwo.backend import settings as backend_settings

    tries = attempts if attempts is not None else max(1, backend_settings.llm_retries() + 1)
    last: Exception | None = None
    for attempt in range(tries):
        try:
            return reply_text(await run_agent(agent, user_prompt))
        except Exception as exc:  # noqa: BLE001 - retry any transient failure
            last = exc
            if attempt + 1 < tries:
                await asyncio.sleep(0.3 * (2**attempt))
    raise last if last else RuntimeError("agent call failed")


def reply_text(result: Any) -> str:
    """Best-effort text extraction from whatever the backend runner returned."""
    if result is None:
        return ""
    if isinstance(result, dict):
        for key in ("output", "content", "answer", "result"):
            value = result.get(key)
            if isinstance(value, str):
                return value
        return ""
    return getattr(result, "content", None) or str(result)


def extract_json(text: str) -> dict[str, Any]:
    """Parse the first JSON object in ``text`` (tolerant of prose/fences)."""
    if not text:
        return {}
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}
