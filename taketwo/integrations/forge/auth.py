"""Forge credentials (the GitHub App). The forge owns these; ``backend`` never sees them."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def token() -> str:
    return os.getenv("GITHUB_TOKEN", "")


def webhook_secret() -> str:
    return os.getenv("GITHUB_WEBHOOK_SECRET", "")


def configured() -> bool:
    return bool(token())
