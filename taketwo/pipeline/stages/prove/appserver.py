"""Start/stop the app under test for the patched proof re-run (best-effort).

The app is served from a fresh checkout with the fix applied, on a known URL; the
proof re-run points the browser there and checks whether the failure signal is gone.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen


@dataclass
class App:
    proc: subprocess.Popen
    url: str


def _ready(url: str) -> bool:
    try:
        with urlopen(url, timeout=2):
            return True
    except Exception:
        return False


def start(command: str, cwd: str | Path, url: str, timeout: float = 30.0) -> App | None:
    """Start ``command`` in ``cwd`` and wait until ``url`` responds (or ``None``)."""
    if not command:
        return None
    try:
        proc = subprocess.Popen(
            command, cwd=str(cwd), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        return None

    deadline = time.time() + timeout
    while time.time() < deadline:
        if _ready(url):
            return App(proc, url)
        if proc.poll() is not None:
            return None
        time.sleep(0.5)

    stop(App(proc, url))
    return None


def stop(app: App | None) -> None:
    """Terminate the app process (best-effort)."""
    if app is None:
        return
    try:
        app.proc.terminate()
        app.proc.wait(timeout=10)
    except Exception:
        try:
            app.proc.kill()
        except Exception:
            pass
