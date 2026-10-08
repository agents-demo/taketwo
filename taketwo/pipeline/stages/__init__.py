"""The pipeline stages, in execution order.

The order is data here (and enforced by ``tests/unit/test_architecture.py``) rather
than encoded in folder names, so it is importable and stays in one place:

    01 understand  -> 02 reproduce -> 03 repair -> 04 prove -> 05 deliver

Side-effect free at import time.
"""

STAGES = ("understand", "reproduce", "repair", "prove", "deliver")

__all__ = ["STAGES"]
