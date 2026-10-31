"""Production entry point: serve the UI with waitress on loopback.

Caddy is what faces the internet; this binds 127.0.0.1 unless told otherwise.
Threads are generous because a plan or chat call blocks its request on
``claude -p`` for up to five minutes.
"""

from __future__ import annotations

import logging
import os

from waitress import serve

from ui.app import app

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8086


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    host = os.environ.get("PACE_AI_HOST") or DEFAULT_HOST
    port = int(os.environ.get("PACE_AI_PORT") or DEFAULT_PORT)
    logging.getLogger(__name__).info("serving on http://%s:%d", host, port)
    serve(app, host=host, port=port, threads=8)


if __name__ == "__main__":
    main()
