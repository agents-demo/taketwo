"""Flatten openjiuwen messages/tool calls into clipped, JSON-safe text for tracing."""

from __future__ import annotations

import json
from typing import Any


def _clip(text: Any, limit: int | None = 8000) -> str:
    text = str(text or "")
    if limit is None or len(text) <= limit:
        return text
    return text[:limit] + f"\n… (+{len(text) - limit} more chars)"


def _content_text(content: Any) -> str:
    """Flatten a message content (str or OpenAI-style parts) to text, images summarised."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        images = 0
        for part in content:
            if isinstance(part, dict):
                kind = part.get("type")
                if kind == "text":
                    parts.append(str(part.get("text", "")))
                elif kind in ("image_url", "image"):
                    images += 1
                else:
                    parts.append(str(part))
            else:
                parts.append(str(part))
        text = "\n".join(parts)
        if images:
            label = "[image]" if images == 1 else f"[image ×{images}]"
            text = (text + "\n" if text else "") + label
        return text
    return str(content or "")


def _iter_image_urls(messages: Any) -> list[str]:
    urls: list[str] = []
    if messages is None:
        return urls
    if isinstance(messages, (str, dict)) or not hasattr(messages, "__iter__"):
        messages = [messages]
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") not in ("image_url", "image"):
                continue
            ref = part.get("image_url") or part.get("image") or {}
            url = ref.get("url") if isinstance(ref, dict) else ref
            if isinstance(url, str) and url.startswith("data:image") and ";base64," in url:
                urls.append(url)
    return urls


def _tool_call_names(raw: Any) -> list[str]:
    names = []
    for call in raw or []:
        name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
        if name:
            names.append(str(name))
    return names


def _message_text(message: Any) -> tuple[str, str]:
    if isinstance(message, dict):
        role = str(message.get("role", "?"))
        text = _content_text(message.get("content", ""))
        names = _tool_call_names(message.get("tool_calls"))
    else:
        role = getattr(message, "role", None) or type(message).__name__
        text = _content_text(getattr(message, "content", ""))
        names = _tool_call_names(getattr(message, "tool_calls", None))
    if names:
        text = (text + "\n" if text else "") + f"[requested tools: {', '.join(names)}]"
    return str(role), text


def sanitize_messages(messages: Any, limit: int | None = 8000) -> list[dict]:
    """Messages as ``[{role, content}]``; images elided, text clipped only if ``limit`` set."""
    if messages is None:
        return []
    if isinstance(messages, (str, dict)) or not hasattr(messages, "__iter__"):
        messages = [messages]
    out = []
    for message in messages:
        role, text = _message_text(message)
        out.append({"role": role, "content": _clip(text, limit)})
    return out


def _as_text(value: Any, limit: int | None = 4000) -> str:
    if isinstance(value, (dict, list, tuple)):
        try:
            return _clip(json.dumps(value, ensure_ascii=False, default=str, indent=2), limit)
        except Exception:
            pass
    return _clip(value, limit)


def _tool_calls(raw: Any) -> list[dict]:
    out = []
    for call in raw or []:
        if isinstance(call, dict):
            name, arguments = call.get("name"), call.get("arguments")
        else:
            name, arguments = getattr(call, "name", None), getattr(call, "arguments", None)
        entry: dict = {"name": str(name or "")}
        if arguments:
            entry["arguments"] = _clip(arguments, 2000)
        out.append(entry)
    return out


_INTERNAL_ARGS = {"session", "self", "cls", "ctx", "context"}


def _tool_arguments(inputs: Any) -> str:
    try:
        args, kwargs = inputs
        kwargs = {
            key: value
            for key, value in (kwargs or {}).items()
            if key not in _INTERNAL_ARGS and isinstance(value, (str, int, float, bool, list, dict, type(None)))
        }
        if not args:
            payload: Any = kwargs
        elif not kwargs:
            payload = list(args)
        else:
            payload = {"args": [a for a in args if isinstance(a, (str, int, float, bool, list, dict))], "kwargs": kwargs}
        return _as_text(payload, 4000)
    except Exception:
        return _clip(str(inputs), 4000)
