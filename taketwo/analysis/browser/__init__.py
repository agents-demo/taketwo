"""Shared browser primitives: a Playwright session wrapper (open, act, console, record).

Used by 2+ stages (``reproduce`` and ``prove``). Everything degrades to a
no-browser session when Playwright is not installed, so the pipeline still runs.
"""

from taketwo.analysis.browser.session import BrowserSession, open_session

__all__ = ["BrowserSession", "open_session"]
