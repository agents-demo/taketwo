"""A thin browser session over Playwright (or a no-op session when unavailable).

The session is the analogue of topspin's vision agent in the run state: opened once
per run, shared by the ``reproduce`` and ``prove`` stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from taketwo import config


@dataclass
class StepResult:
    action: str
    target: str
    ok: bool = True
    detail: str = ""


@dataclass
class BrowserSession:
    """Drive a real browser, or record steps without one when Playwright is absent."""

    app_url: str
    headless: bool = True
    live: bool = False
    _page: Any = None
    _context: Any = None
    _playwright: Any = None
    console: list[str] = field(default_factory=list)
    network: list[str] = field(default_factory=list)

    def open(self) -> bool:
        """Launch the browser (returns ``False`` and stays degraded on any error)."""
        if not self.app_url:
            self.live = False
            self.console.append("browser unavailable: no app url provided")
            return False
        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            browser = self._playwright.chromium.launch(headless=self.headless)
            self._context = browser.new_context(record_video_dir=None)
            self._page = self._context.new_page()
            self._page.on("console", lambda msg: self.console.append(f"{msg.type}: {msg.text}"))
            self._page.on("pageerror", lambda err: self.console.append(f"pageerror: {err}"))
            self._page.goto(self.app_url, wait_until="domcontentloaded", timeout=int(config.step_timeout() * 1000))
            self.live = True
            return True
        except Exception as exc:
            self.live = False
            self.console.append(f"browser unavailable: {exc}")
            return False

    def act(self, action: str, target: str = "", value: str = "") -> StepResult:
        """Perform one step; a no-op success when there is no live browser."""
        if not self.live or self._page is None:
            return StepResult(action, target, ok=True, detail="no-browser")
        try:
            if action == "click" and target:
                self._page.click(target, timeout=int(config.step_timeout() * 1000))
            elif action == "type" and target:
                self._page.fill(target, value)
            elif action == "navigate" and value:
                self._page.goto(value, wait_until="domcontentloaded")
            elif action == "wait":
                self._page.wait_for_timeout(500)
            return StepResult(action, target, ok=True)
        except Exception as exc:
            return StepResult(action, target, ok=False, detail=str(exc))

    def snapshot(self, path: str | Path) -> str | None:
        if not self.live or self._page is None:
            return None
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception:
            return None

    def close(self) -> None:
        for closer in (getattr(self._context, "close", None), getattr(self._playwright, "stop", None)):
            try:
                if closer:
                    closer()
            except Exception:
                pass


def open_session(app_url: str, headless: bool = True) -> BrowserSession:
    """Open a browser session for ``app_url`` (degraded when Playwright is absent)."""
    session = BrowserSession(app_url=app_url, headless=headless)
    session.open()
    return session
