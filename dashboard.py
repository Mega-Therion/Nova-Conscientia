"""Lightweight web dashboard for Nova Conscientia (stdlib only, no dependencies).

Serves a single-page dashboard on port 3000 showing project overview,
benchmark receipts, and the epistemic ledger.  Uses only Python's standard
library.

Page rendering lives in ``dashboard_page.py``; this module handles the
HTTP server and the read-only receipt endpoint.
"""

from __future__ import annotations

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from dashboard_page import render_dashboard

REPO_ROOT = Path(__file__).resolve().parent
PORT = 3000


# --------------------------------------------------------------------------- #
#  Data helpers
# --------------------------------------------------------------------------- #

def _load_receipt() -> dict | None:
    """Load the committed benchmark receipt if it exists."""
    path = REPO_ROOT / "benchmarks" / "results" / "benchmark_receipt.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _git_hash() -> str:
    """Return the short git commit hash, or 'unknown'.

    Reads directly from the .git directory so it works even when the
    ``git`` binary is not installed (e.g. python:3.12-slim).
    """
    git_dir = REPO_ROOT / ".git"
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref_path = git_dir / head[4:].strip()
            if ref_path.exists():
                full = ref_path.read_text(encoding="utf-8").strip()
            else:
                # packed-refs fallback
                packed = git_dir / "packed-refs"
                if packed.exists():
                    ref_name = head[4:].strip()
                    for line in packed.read_text(encoding="utf-8").splitlines():
                        if line.strip().endswith(ref_name):
                            full = line.split()[0]
                            break
                    else:
                        return "unknown"
                else:
                    return "unknown"
        else:
            full = head  # detached HEAD — raw hash
        return full[:7]
    except Exception:
        return "unknown"


# --------------------------------------------------------------------------- #
#  HTTP handler
# --------------------------------------------------------------------------- #

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            html = render_dashboard(_load_receipt(), _git_hash())
            self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))

        elif path == "/api/receipt":
            receipt = _load_receipt()
            if receipt:
                self._send_json(200, receipt)
            else:
                self._send_json(404, {"error": "No benchmark receipt found"})

        else:
            self._send_json(404, {"error": "Not found"})

    def _send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code, obj):
        body = json.dumps(obj, indent=2, default=str).encode("utf-8")
        self._send(code, "application/json", body)

    def log_message(self, *args):
        pass  # quiet


def main():
    host = os.environ.get("NOVA_HOST", "127.0.0.1")
    server = HTTPServer((host, PORT), Handler)
    print(f"Nova Conscientia dashboard serving on http://{host}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
