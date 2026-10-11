"""Serve a demo scenario's app for a live reproduction.

    python demo/serve_scenario.py [scenario] [port]     # default: booking 3000
"""

from __future__ import annotations

import http.server
import socketserver
import sys
from functools import partial

from _scenario import app_dir


def main(scenario: str = "booking", port: int = 3000) -> int:
    root = app_dir(scenario)
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"serving {root} at http://localhost:{port}  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(main(args[0] if args else "booking", int(args[1]) if len(args) > 1 else 3000))
