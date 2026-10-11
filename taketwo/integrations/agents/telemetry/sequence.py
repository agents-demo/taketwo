"""A process-wide monotonic sequence, so model and tool calls can be ordered exactly."""

from __future__ import annotations

import itertools
import threading

_SEQ = itertools.count(1)
_SEQ_LOCK = threading.Lock()


def next_seq() -> int:
    with _SEQ_LOCK:
        return next(_SEQ)
