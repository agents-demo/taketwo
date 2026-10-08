"""Forge credentials (the GitHub App). The forge owns these; ``backend`` never sees them."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def token() -> str:
    return os.getenv("GITHUB_TOKEN", "")


def default_repo() -> str:
    owner, name = os.getenv("GITHUB_OWNER", ""), os.getenv("GITHUB_REPO", "")
    return f"{owner}/{name}" if owner and name else ""


def configured() -> bool:
    return bool(token())
