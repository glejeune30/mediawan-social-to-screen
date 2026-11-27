"""Story Radar — local web server for the interface in web/ (Python standard library only).

Run:  python server.py            then open http://localhost:8600
      python server.py --port 8700  (another port)

Endpoints:
  GET  /              the interface (web/index.html)
  GET  /api/status    state of the data refresh
  POST /api/refresh   collects this week's data and rebuilds web/data/radar.json, in the
                      background (scripts/run_watchlist.py, about 10 minutes)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
STATUS = {"running": False, "step": "", "ok": None, "started": None, "finished": None, "log": ""}
LOCK = threading.Lock()


# progress lines printed by scripts/run_watchlist.py -> label shown on the button
STEPS = {
    "1/4": "1/4 · AniList : webtoons en tendance…",
    "2/4": "2/4 · Open Library : romans récents…",
    "3/4": "3/4 · Wikipedia : pages et vues…",
    "4/4": "4/4 · Calcul des scores…",
    "saved ": "Mise à jour de l'interface…",
}


def refresh_job() -> None:
    """Runs scripts/run_watchlist.py (collect + score + web/data/radar.json) and follows its progress."""
    STATUS.update(running=True, ok=None, step="Démarrage…", started=time.time(), finished=None, log="")
    log: list[str] = []
    try:
        p = subprocess.Popen([sys.executable, "-X", "utf8", "-u", str(ROOT / "scripts" / "run_watchlist.py")],
                             cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
        for line in p.stdout:
            log.append(line)
            for key, label in STEPS.items():
                if line.strip().startswith(key):
                    STATUS["step"] = label
        ok = p.wait() == 0
    except OSError as exc:
        log.append(str(exc))
        ok = False
    STATUS.update(running=False, ok=ok, step="", finished=time.time(), log="".join(log)[-3000:])


class Handler(SimpleHTTPRequestHandler):
    # Windows can map .js to text/plain, which browsers refuse for modules: set the types here.
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript",
                      ".mjs": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml",
                      ".json": "application/json", ".html": "text/html"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/status"):
            return self._json(STATUS)
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/refresh"):
            with LOCK:
                if not STATUS["running"]:
                    STATUS["running"] = True
                    threading.Thread(target=refresh_job, daemon=True).start()
            return self._json({"started": True}, 202)
        self.send_error(404)

    def end_headers(self):
        # always serve fresh files: the data and the code change while you work
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Story Radar local server")
    # 8600, not Streamlit's 8501: the old prototype can still run beside it without clashing
    ap.add_argument("--port", type=int, default=8600)
    ap.add_argument("--host", default="127.0.0.1", help="127.0.0.1 = only this computer")
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Story Radar: http://localhost:{args.port}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
