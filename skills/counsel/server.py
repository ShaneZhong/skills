"""Counsel — AI Board Meeting Server

Serves the interactive UI and provides SSE endpoints for real-time advisor updates.
Usage: python server.py [--port 8787] [--session SESSION_DIR]
"""

import argparse
import errno
import json
import os
import queue
import socket
import sys
import tempfile
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn

SKILL_DIR = Path(__file__).parent
TEMPLATE_DIR = SKILL_DIR / "templates"
ADVISORS_FILE = SKILL_DIR / "advisors.json"
SESSION_DIR: Path | None = None

# SSE client registry
_event_queues: list[queue.Queue] = []
_queues_lock = threading.Lock()

# Session file access (read-modify-write guard)
_session_lock = threading.Lock()

# Monotonic event ID for SSE de-dup / reconnect
_event_counter = 0
_event_counter_lock = threading.Lock()

# Ring buffer of recent events for Last-Event-ID replay
_event_history: list[tuple[int, str, str]] = []  # (id, event_name, data_json)
_history_lock = threading.Lock()
HISTORY_MAX = 500


def _next_event_id() -> int:
    global _event_counter
    with _event_counter_lock:
        _event_counter += 1
        return _event_counter


def _remember_event(eid: int, event_name: str, data_json: str) -> None:
    with _history_lock:
        _event_history.append((eid, event_name, data_json))
        if len(_event_history) > HISTORY_MAX:
            del _event_history[: len(_event_history) - HISTORY_MAX]


def broadcast(event_name: str, data: dict) -> None:
    """Send an SSE event to all connected clients."""
    eid = _next_event_id()
    data_json = json.dumps(data, ensure_ascii=False)
    msg = f"id: {eid}\nevent: {event_name}\ndata: {data_json}\n\n"
    _remember_event(eid, event_name, data_json)
    with _queues_lock:
        dead: list[queue.Queue] = []
        for q in _event_queues:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _event_queues.remove(q)


def replay_events_since(last_id: int) -> list[str]:
    with _history_lock:
        return [
            f"id: {eid}\nevent: {name}\ndata: {payload}\n\n"
            for eid, name, payload in _event_history
            if eid > last_id
        ]


def atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically using rename. Prevents torn reads."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".session.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


class CounselHandler(SimpleHTTPRequestHandler):
    server_version = "Counsel/0.2"

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._serve_file(TEMPLATE_DIR / "index.html", "text/html")
        elif self.path == "/api/advisors":
            self._serve_file(ADVISORS_FILE, "application/json")
        elif self.path == "/api/session":
            self._serve_session()
        elif self.path == "/api/events":
            self._serve_sse()
        else:
            self.send_error(404)

    def do_POST(self):  # noqa: N802
        if self.path != "/api/update":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > 1_000_000:
            self._send_json(400, {"ok": False, "error": "invalid content length"})
            return

        raw = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_json(400, {"ok": False, "error": f"invalid json: {e}"})
            return

        if not isinstance(body, dict) or "type" not in body:
            self._send_json(400, {"ok": False, "error": "missing 'type' field"})
            return

        try:
            self._handle_update(body)
        except Exception as e:
            self._send_json(500, {"ok": False, "error": f"handler failed: {e}"})
            return

        self._send_json(200, {"ok": True})

    # --- helpers ---

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self, path: Path, content_type: str):
        if not path.is_file():
            self.send_error(404)
            return
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def _serve_session(self):
        session_file = SESSION_DIR / "session.json"
        with _session_lock:
            if session_file.exists():
                data = session_file.read_bytes()
            else:
                data = json.dumps({"status": "waiting"}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _serve_sse(self):
        try:
            last_id = int(self.headers.get("Last-Event-ID", "0") or "0")
        except ValueError:
            last_id = 0

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        q: queue.Queue = queue.Queue(maxsize=1000)
        with _queues_lock:
            _event_queues.append(q)
        try:
            # Replay missed events after reconnect
            for msg in replay_events_since(last_id):
                self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()

            while True:
                try:
                    msg = q.get(timeout=15)
                except queue.Empty:
                    # Heartbeat comment line (SSE spec) — keeps the connection alive
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue
                self.wfile.write(msg.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            pass
        finally:
            with _queues_lock:
                if q in _event_queues:
                    _event_queues.remove(q)

    def _handle_update(self, body: dict):
        event_type = body.get("type", "unknown")
        data = body.get("data")
        session_file = SESSION_DIR / "session.json"

        with _session_lock:
            if session_file.exists():
                session = json.loads(session_file.read_text(encoding="utf-8"))
            else:
                session = {
                    "status": "running",
                    "statements": [],
                    "advisor_questions": [],
                    "debates": [],
                    "chat": [],
                    "synthesis": None,
                }

            if event_type == "init":
                session["question"] = body.get("question", "")
                session["status"] = "clarifying"
                session["timestamp"] = body.get("timestamp", "")

            elif event_type == "advisor_question":
                lst = session.setdefault("advisor_questions", [])
                # Idempotent: replace on duplicate advisor_id
                aid = (data or {}).get("advisor_id")
                if aid:
                    lst[:] = [x for x in lst if x.get("advisor_id") != aid]
                lst.append(data or {})
                session["status"] = "questions"

            elif event_type == "advisor_statement":
                lst = session.setdefault("statements", [])
                aid = (data or {}).get("advisor_id")
                if aid:
                    lst[:] = [x for x in lst if x.get("advisor_id") != aid]
                lst.append(data or {})
                session["status"] = "statements"

            elif event_type == "dimensions":
                session["dimensions"] = data or []
                session["status"] = "dimensions"

            elif event_type == "debate":
                session.setdefault("debates", []).append(data or {})
                session["status"] = "debating"

            elif event_type == "premortem":
                session["premortem"] = data or {}

            elif event_type == "synthesis":
                session["synthesis"] = data or {}
                session["status"] = "complete"

            elif event_type == "chat":
                session.setdefault("chat", []).append(data or {})

            elif event_type == "status":
                session["status"] = body.get("status", session.get("status", "running"))

            else:
                raise ValueError(f"unknown event type: {event_type}")

            atomic_write_json(session_file, session)

        broadcast(event_type, data if data is not None else body)

    def log_message(self, format, *args):  # noqa: A002
        pass


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _pick_port(preferred: int, tries: int = 20) -> int:
    """Probe ports starting at `preferred`, return the first free one."""
    for offset in range(tries):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError as e:
                if e.errno in (errno.EADDRINUSE, errno.EACCES):
                    continue
                raise
    raise RuntimeError(f"no free port in range {preferred}..{preferred + tries - 1}")


def main():
    global SESSION_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--session", type=str, required=True)
    parser.add_argument("--strict-port", action="store_true",
                        help="fail if --port is taken (default: auto-probe next)")
    args = parser.parse_args()

    SESSION_DIR = Path(args.session).resolve()
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    port = args.port if args.strict_port else _pick_port(args.port)

    server = ThreadingHTTPServer(("127.0.0.1", port), CounselHandler)

    pid_file = SESSION_DIR / "server.pid"
    url_file = SESSION_DIR / "server.url"
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    url_file.write_text(f"http://localhost:{port}", encoding="utf-8")

    print(f"COUNSEL_URL=http://localhost:{port}")
    print(f"COUNSEL_PID={os.getpid()}")
    print(f"Session: {SESSION_DIR}")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        for f in (pid_file, url_file):
            try:
                f.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    main()
