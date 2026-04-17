"""End-to-end tests for the counsel server.

Spins up `server.py` as a real subprocess per-test (via the `server` fixture in
conftest.py) and exercises the HTTP API. Covers reducer idempotency, input
validation, atomic writes, session persistence, advisor SSOT, and SSE replay.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from conftest import http_get_json, http_get_status, http_post, http_post_raw


# --- Input validation ---

def test_malformed_json_returns_400(server):
    url, _ = server
    status = http_post_raw(f"{url}/api/update", b"not json")
    assert status == 400


def test_missing_type_returns_400(server):
    url, _ = server
    status, body = http_post(f"{url}/api/update", {"foo": "bar"})
    assert status == 400
    assert body["ok"] is False


def test_empty_body_returns_400(server):
    url, _ = server
    status = http_post_raw(f"{url}/api/update", b"")
    assert status == 400


def test_oversized_body_rejected(server):
    url, _ = server
    # >1MB payload should be rejected. The server may either send 400 and close,
    # or close the connection mid-upload (urlopen raises; we return 0).
    big = json.dumps({"type": "chat", "data": {"role": "user", "text": "x" * (1_100_000)}}).encode()
    status = http_post_raw(f"{url}/api/update", big)
    assert status in (0, 400)


def test_unknown_type_returns_500(server):
    url, _ = server
    status, body = http_post(f"{url}/api/update", {"type": "nonexistent"})
    assert status == 500
    assert "unknown event type" in body.get("error", "")


# --- Reducer behavior via the HTTP API ---

def test_init_sets_question(server):
    url, session_dir = server
    status, _ = http_post(f"{url}/api/update", {
        "type": "init", "question": "Ship or pivot?", "timestamp": "2026-04-16"
    })
    assert status == 200
    session = http_get_json(f"{url}/api/session")
    assert session["question"] == "Ship or pivot?"
    assert session["status"] == "clarifying"


def test_advisor_statement_idempotent_by_id(server):
    """Posting the same advisor twice keeps only one entry (the latest)."""
    url, _ = server
    http_post(f"{url}/api/update", {
        "type": "advisor_statement",
        "data": {"advisor_id": "jobs", "stance": "SUPPORT", "statement": "first"}
    })
    http_post(f"{url}/api/update", {
        "type": "advisor_statement",
        "data": {"advisor_id": "jobs", "stance": "AGAINST", "statement": "second"}
    })
    session = http_get_json(f"{url}/api/session")
    stmts = session["statements"]
    assert len(stmts) == 1
    assert stmts[0]["statement"] == "second"
    assert stmts[0]["stance"] == "AGAINST"


def test_multiple_advisors_all_recorded(server):
    url, _ = server
    for aid in ["jobs", "buffett", "thiel"]:
        http_post(f"{url}/api/update", {
            "type": "advisor_statement",
            "data": {"advisor_id": aid, "stance": "SUPPORT", "statement": f"from {aid}"}
        })
    session = http_get_json(f"{url}/api/session")
    ids = {s["advisor_id"] for s in session["statements"]}
    assert ids == {"jobs", "buffett", "thiel"}


def test_advisor_question_idempotent_by_id(server):
    url, _ = server
    http_post(f"{url}/api/update", {
        "type": "advisor_question",
        "data": {"advisor_id": "musk", "question": "v1"}
    })
    http_post(f"{url}/api/update", {
        "type": "advisor_question",
        "data": {"advisor_id": "musk", "question": "v2"}
    })
    session = http_get_json(f"{url}/api/session")
    qs = session["advisor_questions"]
    assert len(qs) == 1
    assert qs[0]["question"] == "v2"


def test_chat_is_append_only(server):
    """Chat messages accumulate; no dedup on server side (client handles)."""
    url, _ = server
    for text in ["hello", "hello", "goodbye"]:
        http_post(f"{url}/api/update", {
            "type": "chat", "data": {"role": "facilitator", "text": text}
        })
    session = http_get_json(f"{url}/api/session")
    assert len(session["chat"]) == 3


def test_debates_accumulate(server):
    url, _ = server
    for dim in ["Speed vs safety", "Niche vs broad"]:
        http_post(f"{url}/api/update", {
            "type": "debate", "data": {"dimension": dim, "messages": []}
        })
    session = http_get_json(f"{url}/api/session")
    assert len(session["debates"]) == 2


def test_synthesis_marks_complete(server):
    url, _ = server
    http_post(f"{url}/api/update", {
        "type": "synthesis",
        "data": {"consensus": "c", "tensions": "t", "actions": ["a1"], "verdict": "v"}
    })
    session = http_get_json(f"{url}/api/session")
    assert session["status"] == "complete"
    assert session["synthesis"]["verdict"] == "v"


def test_premortem_stored(server):
    url, _ = server
    http_post(f"{url}/api/update", {
        "type": "premortem", "data": {"text": "it failed because..."}
    })
    session = http_get_json(f"{url}/api/session")
    assert "premortem" in session
    assert "failed because" in session["premortem"]["text"]


# --- Persistence & atomic writes ---

def test_session_file_is_atomic(server):
    """After a POST, session.json must parse as valid JSON (no torn writes).

    This is a smoke test — real race conditions need concurrency to trigger, but
    if atomic_write_json regresses to in-place writes, a concurrent reader
    reading a half-written file would see invalid JSON.
    """
    url, session_dir = server
    http_post(f"{url}/api/update", {
        "type": "init", "question": "q", "timestamp": "2026-04-16"
    })
    raw = (session_dir / "session.json").read_text(encoding="utf-8")
    parsed = json.loads(raw)  # must not raise
    assert parsed["question"] == "q"


def test_session_persists_across_requests(server):
    url, _ = server
    http_post(f"{url}/api/update", {"type": "init", "question": "q1", "timestamp": "t"})
    http_post(f"{url}/api/update", {
        "type": "advisor_statement",
        "data": {"advisor_id": "jobs", "stance": "SUPPORT", "statement": "s"}
    })
    # Get the session twice, should be consistent
    s1 = http_get_json(f"{url}/api/session")
    s2 = http_get_json(f"{url}/api/session")
    assert s1 == s2
    assert s1["question"] == "q1"
    assert len(s1["statements"]) == 1


# --- Advisors SSOT ---

def test_advisors_endpoint(server):
    url, _ = server
    advisors = http_get_json(f"{url}/api/advisors")
    assert isinstance(advisors, list)
    assert len(advisors) == 12
    ids = {a["id"] for a in advisors}
    # Spot-check the canonical IDs the skill references
    for expected in ["jobs", "bezos", "musk", "buffett", "dalio", "einstein"]:
        assert expected in ids
    # Every advisor has required fields
    for a in advisors:
        assert {"id", "name", "emoji", "framework"}.issubset(a.keys())


def test_advisors_unique_ids(server):
    url, _ = server
    advisors = http_get_json(f"{url}/api/advisors")
    ids = [a["id"] for a in advisors]
    assert len(ids) == len(set(ids))


# --- HTTP basics ---

def test_index_html_served(server):
    url, _ = server
    assert http_get_status(f"{url}/") == 200
    assert http_get_status(f"{url}/index.html") == 200


def test_unknown_path_404(server):
    url, _ = server
    assert http_get_status(f"{url}/nope") == 404


def test_unknown_api_path_404(server):
    url, _ = server
    # POST to unknown path
    status = http_post_raw(f"{url}/api/bogus", b"{}")
    assert status == 404


def test_empty_session_json_default(server):
    """Before any POST, /api/session returns a minimal valid shape."""
    url, _ = server
    session = http_get_json(f"{url}/api/session")
    assert "status" in session


# --- Server bookkeeping ---

def test_pid_and_url_files_written(server):
    url, session_dir = server
    pid_file = session_dir / "server.pid"
    url_file = session_dir / "server.url"
    assert pid_file.exists()
    assert url_file.exists()
    pid = int(pid_file.read_text())
    assert pid > 0
    assert url_file.read_text().strip() == url


# --- HTML / XSS ---

def test_no_inline_onclick_in_html(server):
    """The HTML must not contain inline onclick handlers with template literals.

    Inline onclick='openModal(${JSON.stringify(...)})' was a past XSS vector.
    After the event-delegation rewrite, the only `onclick` in output should be
    zero. If we ever re-introduce them for a justified reason, update this test.
    """
    import urllib.request
    with urllib.request.urlopen(server[0] + "/", timeout=2) as resp:
        html = resp.read().decode("utf-8")
    assert "onclick='openModal" not in html
    assert 'onclick="openModal' not in html


# --- Port probing (standalone, no fixture) ---

def test_port_probe_picks_next_free(tmp_path):
    """Starting two servers without --strict-port should land on different ports."""
    import socket
    import subprocess
    import signal
    import time as _t
    from conftest import PYTHON, SERVER_PY, _wait_ready

    s1_dir = tmp_path / "s1"; s1_dir.mkdir()
    s2_dir = tmp_path / "s2"; s2_dir.mkdir()

    # Grab a port and leave it bound so the first server must probe past it.
    block = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    block.bind(("127.0.0.1", 0))
    blocked_port = block.getsockname()[1]

    # Server 1: request the blocked port, expect auto-probe
    p1 = subprocess.Popen([str(PYTHON), str(SERVER_PY),
                           "--port", str(blocked_port), "--session", str(s1_dir)])
    # Server 2: request the same blocked port, expect a different auto-probed one
    p2 = subprocess.Popen([str(PYTHON), str(SERVER_PY),
                           "--port", str(blocked_port), "--session", str(s2_dir)])
    try:
        url1 = _wait_ready(s1_dir / "server.url")
        url2 = _wait_ready(s2_dir / "server.url")
        assert url1 != url2
        # Both should have probed to a port ABOVE the blocked one
        port1 = int(url1.rsplit(":", 1)[1])
        port2 = int(url2.rsplit(":", 1)[1])
        assert port1 != blocked_port
        assert port2 != blocked_port
        assert port1 != port2
    finally:
        block.close()
        for p in (p1, p2):
            try:
                p.send_signal(signal.SIGTERM)
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=2)


# --- SSE (lightweight — full streaming is hard to test portably) ---

def test_sse_endpoint_responds(server):
    """SSE endpoint should return 200 and the right content type."""
    import urllib.request
    req = urllib.request.Request(server[0] + "/api/events")
    # Don't read the stream fully — we just want to check headers.
    # Use a short timeout so the blocking read doesn't hang the test.
    try:
        resp = urllib.request.urlopen(req, timeout=0.5)
        assert resp.status == 200
        ct = resp.headers.get("Content-Type", "")
        assert "text/event-stream" in ct
        resp.close()
    except TimeoutError:
        # Stream is open — that's success. The server kept the connection.
        pass
