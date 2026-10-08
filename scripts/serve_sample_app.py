"""Serve the sample buggy app so a reproduction can run against a real page.

    python scripts/serve_sample_app.py [port]      # default: http://localhost:3000

Then:  taketwo record <clip> --app http://localhost:3000
"""

from __future__ import annotations

import http.server
import socketserver
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "examples" / "sample_app"


def main(port: int = 3000) -> int:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"serving {ROOT} at http://localhost:{port}  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 3000))
