#!/usr/bin/env python3
"""Tests for http_util — the stdlib HTTP shim that lets OpenVera ship with zero
third-party dependencies (replacing `requests`).

The contract under test: a requests-compatible slice (get/post returning a
Response with status_code/text/json()), HTTP error statuses returned as a
Response rather than raised, params encoding, and transport failures surfaced as
ConnectionError/Timeout. Exercised against a local http.server — no network.

Stdlib unittest, runs on macOS system Python 3.9.6:

    python3 -m unittest discover -s tests
    python3 tests/test_http_util.py
"""
import json
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "vera-system" / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import http_util  # noqa: E402


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence test noise
        pass

    def _respond(self, method):
        # /status/NNN -> echo that status code. /slow -> sleep. else 200 echo.
        if self.path.startswith("/status/"):
            code = int(self.path.rsplit("/", 1)[1])
        elif self.path.startswith("/slow"):
            time.sleep(1.0)
            code = 200
        else:
            code = 200
        length = int(self.headers.get("Content-Length", 0))
        body_in = self.rfile.read(length) if length else b""
        payload = json.dumps({
            "method": method,
            "path": self.path,
            "body": body_in.decode("utf-8") if body_in else None,
        }).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._respond("GET")

    def do_POST(self):
        self._respond("POST")


class HttpUtilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.host, cls.port = cls.server.server_address
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_returns_response_with_status_text_json(self):
        r = http_util.get(self.base + "/hello", timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertIn("GET", r.text)
        self.assertEqual(r.json()["method"], "GET")

    def test_post_sends_json_body(self):
        r = http_util.post(self.base + "/echo", json={"a": 1}, timeout=5)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["method"], "POST")
        self.assertEqual(json.loads(data["body"]), {"a": 1})

    def test_error_status_returned_not_raised(self):
        # 4xx/5xx must come back as a Response (like requests), so callers can
        # branch on status_code (401/402/429/5xx) instead of catching.
        for code in (401, 404, 500):
            r = http_util.get(self.base + f"/status/{code}", timeout=5)
            self.assertEqual(r.status_code, code)

    def test_params_are_encoded_onto_url(self):
        r = http_util.get(self.base + "/search", params={"key": "a b", "n": 2}, timeout=5)
        path = r.json()["path"]
        self.assertIn("key=a+b", path)
        self.assertIn("n=2", path)

    def test_connection_error_on_refused_port(self):
        # Nothing listening on this port -> connection refused -> ConnectionError.
        with self.assertRaises(http_util.ConnectionError):
            http_util.get("http://127.0.0.1:9", timeout=2)

    def test_timeout_is_raised(self):
        with self.assertRaises(http_util.Timeout):
            http_util.get(self.base + "/slow", timeout=0.3)

    def test_requests_compatible_exception_surface(self):
        # Both specific errors derive from RequestException, mirroring requests,
        # so `except requests.RequestException` keeps catching everything.
        self.assertTrue(issubclass(http_util.ConnectionError, http_util.RequestException))
        self.assertTrue(issubclass(http_util.Timeout, http_util.RequestException))


if __name__ == "__main__":
    unittest.main()
