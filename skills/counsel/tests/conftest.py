"""Shared pytest fixtures for counsel server tests.

Each test that needs a running server uses the `server` fixture:
- picks a random high port
- spawns server.py as a subprocess with --session <tmp>
- waits for server.url file to appear
- yields (base_url, session_dir)
- on teardown, kills the subprocess and waits
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
SERVER_PY = SKILL_DIR / "server.py"
PYTHON = Path("/Users/shane/Documents/playground/.venv/bin/python3")
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_ready(url_file: Path, timeout: float = 5.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if url_file.exists():
            url = url_file.read_text(encoding="utf-8").strip()
            if url:
                return url
        time.sleep(0.05)
    raise TimeoutError(f"server did not write {url_file} within {timeout}s")


@pytest.fixture
def server(tmp_path):
    """Launch the counsel server in a subprocess on a free port.

    Yields (base_url, session_dir). Kills the server on teardown.
    """
    port = _free_port()
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    proc = subprocess.Popen(
        [str(PYTHON), str(SERVER_PY), "--port", str(port),
         "--session", str(session_dir), "--strict-port"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        url = _wait_ready(session_dir / "server.url")
        yield url, session_dir
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def http_post(url: str, payload: dict) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=2) as resp:
            return resp.status, json.loads(resp.read())
    except HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def http_post_raw(url: str, raw_body: bytes, content_type: str = "application/json") -> int:
    """Returns HTTP status, or 0 if the server closed the connection (also a rejection)."""
    req = Request(url, data=raw_body, headers={"Content-Type": content_type}, method="POST")
    try:
        with urlopen(req, timeout=2) as resp:
            return resp.status
    except HTTPError as e:
        return e.code
    except (URLError, BrokenPipeError, ConnectionResetError):
        # Server closed before we finished uploading — counts as rejection
        return 0


def http_get_json(url: str) -> dict:
    with urlopen(url, timeout=2) as resp:
        return json.loads(resp.read())


def http_get_status(url: str) -> int:
    try:
        with urlopen(url, timeout=2) as resp:
            return resp.status
    except HTTPError as e:
        return e.code
    except URLError:
        return 0
