"""Minimal stdlib HTTP helper.

OpenVera ships with ZERO third-party dependencies so it installs on any machine
with a working Python 3.8+ — no pip step, no PyPI reachability, no PEP-668
"externally-managed environment" wall, no broken-pip surprises. This module
covers the only HTTP needs the harness has (a JSON POST and a JSON GET, with a
timeout), using nothing but the standard library.

It intentionally mirrors the tiny slice of the `requests` API the scripts used,
so call sites read the same:

    import http_util as requests
    r = requests.post(url, headers=..., json=payload, timeout=120)
    r = requests.get(url, headers=..., params={...}, timeout=10)
    r.status_code      # int
    r.text             # decoded body (str)
    r.json()           # parsed body
    requests.ConnectionError / requests.Timeout / requests.RequestException

HTTP error statuses (4xx/5xx) come back as a normal Response with .status_code
set — exactly like requests — rather than raising, so the existing status-code
branching keeps working.
"""

from __future__ import annotations

import json as _json
import socket
import urllib.error
import urllib.parse
import urllib.request


class RequestException(Exception):
    """Base for transport-level failures (no HTTP response was received)."""


class ConnectionError(RequestException):  # noqa: A001 - mirrors requests.ConnectionError
    """DNS failure, connection refused, or the host was unreachable."""


class Timeout(RequestException):
    """The request exceeded its timeout."""


class Response:
    """A thin stand-in for requests.Response (only what callers use)."""

    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self._body = body

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", "replace")

    def json(self):
        return _json.loads(self._body.decode("utf-8"))


def _request(method, url, headers=None, params=None, json_body=None, timeout=30) -> Response:
    if params:
        sep = "&" if "?" in url else "?"
        url = url + sep + urllib.parse.urlencode(params)

    hdrs = dict(headers or {})
    data = None
    if json_body is not None:
        data = _json.dumps(json_body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Response(resp.getcode(), resp.read())
    except urllib.error.HTTPError as e:
        # 4xx/5xx still carry a status + body. Return it like requests does so
        # the caller's status_code checks (401/402/429/5xx) keep working.
        return Response(e.code, e.read())
    except socket.timeout as e:  # subclass of OSError on 3.8/3.9; TimeoutError alias on 3.10+
        raise Timeout(f"request to {url} timed out after {timeout}s") from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, socket.timeout):
            raise Timeout(f"request to {url} timed out after {timeout}s") from e
        raise ConnectionError(str(reason)) from e


def post(url, headers=None, json=None, timeout=30) -> Response:
    return _request("POST", url, headers=headers, json_body=json, timeout=timeout)


def get(url, headers=None, params=None, timeout=30) -> Response:
    return _request("GET", url, headers=headers, params=params, timeout=timeout)
