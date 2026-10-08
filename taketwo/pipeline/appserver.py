"""Start/stop the app under test (best-effort).

Used by the pipeline prologue (to serve the unpatched app before reproducing) and by
the prove stage (to serve the fix from a fresh checkout). The app is started in its
own process group so the whole tree can be stopped reliably.
"""

from __future__ import annotations

import os
import signal
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


def _popen_kwargs() -> dict:
    """Start the app in its own process group so we can stop the whole tree."""
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def start(command: str, cwd: str | Path, url: str, timeout: float = 30.0) -> App | None:
    """Start ``command`` in ``cwd`` and wait until ``url`` responds (or ``None``)."""
    if not command:
        return None
    try:
        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **_popen_kwargs(),
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
    """Terminate the app and its children (best-effort)."""
    if app is None:
        return
    proc = app.proc
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, check=False)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
