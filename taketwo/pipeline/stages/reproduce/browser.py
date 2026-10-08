"""A thin browser session over Playwright's async API (or a no-op session when unavailable).

Playwright is async so it runs on the pipeline's event loop (the sync API cannot run
inside a running loop). Opened by the reproduce stage and stashed on the run session so
the prove stage re-runs through the same object without importing this module.
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
    _browser: Any = None
    _playwright: Any = None
    console: list[str] = field(default_factory=list)
    network: list[str] = field(default_factory=list)

    async def open(self) -> bool:
        """Launch the browser (returns ``False`` and stays degraded on any error)."""
        if not self.app_url:
            self.console.append("browser unavailable: no app url provided")
            return False
        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            self._page.on("console", lambda msg: self.console.append(f"{msg.type}: {msg.text}"))
            self._page.on("pageerror", lambda err: self.console.append(f"pageerror: {err}"))
            await self._page.goto(self.app_url, wait_until="domcontentloaded", timeout=int(config.step_timeout() * 1000))
            self.live = True
            return True
        except Exception as exc:
            self.live = False
            self.console.append(f"browser unavailable: {exc}")
            return False

    async def act(self, action: str, target: str = "", value: str = "") -> StepResult:
        """Perform one step; a no-op success when there is no live browser."""
        if not self.live or self._page is None:
            return StepResult(action, target, ok=True, detail="no-browser")
        try:
            if action == "click" and target:
                await self._page.click(target, timeout=int(config.step_timeout() * 1000))
            elif action == "type" and target:
                await self._page.fill(target, value)
            elif action == "navigate" and value:
                await self._page.goto(value, wait_until="domcontentloaded")
            elif action == "wait":
                await self._page.wait_for_timeout(500)
            return StepResult(action, target, ok=True)
        except Exception as exc:
            return StepResult(action, target, ok=False, detail=str(exc))

    async def navigate(self, url: str) -> bool:
        """Point the open page at ``url`` (used by the prove re-run on the patched app)."""
        if not self.live or self._page is None or not url:
            return False
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=int(config.step_timeout() * 1000))
            return True
        except Exception:
            return False

    async def outline(self, limit: int = 6000) -> str:
        """A compact accessibility outline of the current page (empty when not live)."""
        if not self.live or self._page is None:
            return ""
        try:
            return (await self._page.locator("body").aria_snapshot())[:limit]
        except Exception:
            return ""

    async def snapshot(self, path: str | Path) -> str | None:
        if not self.live or self._page is None:
            return None
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            await self._page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception:
            return None

    async def close(self) -> None:
        for closer in (
            getattr(self._context, "close", None),
            getattr(self._browser, "close", None),
            getattr(self._playwright, "stop", None),
        ):
            try:
                if closer:
                    await closer()
            except Exception:
                pass


async def open_session(app_url: str, headless: bool = True) -> BrowserSession:
    """Open a browser session for ``app_url`` (degraded when Playwright is absent)."""
    session = BrowserSession(app_url=app_url, headless=headless)
    await session.open()
    return session
