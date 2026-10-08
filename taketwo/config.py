"""Application settings, read from the environment (.env).

Only behaviour that shapes *what the app does* lives here (frame sampling, cursor
thresholds, limits, feature toggles). Anything about reaching model/embedding
endpoints lives in :mod:`taketwo.backend.settings`.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# --- video understanding --------------------------------------------------- #
def frame_fps() -> float:
    """Target frames-per-second when sampling the recording."""
    return float(os.getenv("FRAME_FPS", "2"))


def max_frames() -> int:
    return int(os.getenv("MAX_FRAMES", "12"))


def cursor_threshold() -> float:
    """Pixel-shift below which a frame region is considered still (no cursor move)."""
    return float(os.getenv("CURSOR_MOTION_THRESHOLD", "6"))


# --- reproduction behaviour ------------------------------------------------ #
def agentic_mode() -> bool:
    """Run the model-driven strategy instead of the fixed one."""
    return _bool("AGENTIC_MODE", "false")


def verify_fix() -> bool:
    """Run the acceptance pass (repro red -> green, tests pass) before delivering."""
    return _bool("VERIFY_FIX", "true")


def max_steps() -> int:
    """Cap on replayed steps per reproduction."""
    return int(os.getenv("REPRO_MAX_STEPS", "20"))


def step_timeout() -> float:
    """Per-step timeout (seconds) while replaying in the browser."""
    return float(os.getenv("STEP_TIMEOUT_S", "15"))


# --- proof video ----------------------------------------------------------- #
def proof_width() -> int:
    return int(os.getenv("PROOF_WIDTH", "720"))


def test_command() -> str:
    """Command run in the patched repo to verify the fix (``TEST_COMMAND``; empty = skip)."""
    return os.getenv("TEST_COMMAND", "").strip()


def rails() -> list[str]:
    """Names of the backend rails to enable on agents (``RAILS`` env)."""
    raw = os.getenv("RAILS", "true").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return ["token_budget", "memory"]
    if raw in {"0", "false", "no", "off", ""}:
        return []
    return [name.strip() for name in raw.split(",") if name.strip()]
