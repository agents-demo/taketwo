"""Shared video primitives: frame extraction, cursor/clicks, OCR, clip compositing.

Used by 2+ stages (``understand`` and ``prove``); every third-party import is lazy so
the package imports cleanly without the optional media extras installed.
"""
