"""A real local HTTP server that emulates the Hybrid Analysis API for tests.

No mocks or stubs: this starts an actual WSGI server on an ephemeral localhost
port. The real ``httpx`` client talks to it over real sockets, so the whole
transport, auth, and error-mapping path is exercised end to end.

Behaviour:
* Requests without a valid ``api-key`` header (missing or ``"bad"``) get 401.
* Any path segment ``trigger-404`` / ``trigger-429`` / ``trigger-500`` yields that
  status, letting tests drive every error branch deterministically.
* Paths whose final segment is a known binary artifact return octet-stream bytes;
  everything else returns a JSON echo of the request.
Each handled request is appended to ``server.requests`` for wire-shape assertions.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field
from http import HTTPStatus
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
from wsgiref.types import StartResponse, WSGIEnvironment

VALID_KEY = "test-key"

_BINARY_SUFFIXES = frozenset({"sample", "pcap", "certificate", "download", "dropped-files-v2"})
_BINARY_MARKERS = ("/dropped-file/", "/dropped-file-raw/")
_BINARY_PAYLOAD = b"BINARY-DATA"


@dataclass
class RecordedRequest:
    """One request captured by the server."""

    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    body: bytes = b""
    form: dict[str, list[str]] = field(default_factory=dict)


def _is_binary(path: str) -> bool:
    last = path.rstrip("/").rsplit("/", 1)[-1]
    if last in _BINARY_SUFFIXES:
        return True
    return any(marker in path for marker in _BINARY_MARKERS)


def _error_status(path: str) -> int | None:
    for segment, status in (("trigger-404", 404), ("trigger-429", 429), ("trigger-500", 500)):
        if segment in path:
            return status
    return None


def _headers_from_environ(environ: WSGIEnvironment) -> dict[str, str]:
    headers = {}
    for key, value in environ.items():
        if key.startswith("HTTP_") and isinstance(value, str):
            headers[key[5:].replace("_", "-").lower()] = value
    return headers


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class LocalAPIServer:
    """WSGI server emulating the API; records the requests it handles."""

    def __init__(self) -> None:
        self.requests: list[RecordedRequest] = []
        self._httpd = make_server(
            "127.0.0.1",
            0,
            self._app,
            server_class=_ThreadingWSGIServer,
            handler_class=_QuietHandler,
        )

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._httpd.server_port}"

    def _app(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        method = environ["REQUEST_METHOD"]
        path = environ.get("PATH_INFO", "")
        query = parse_qs(environ.get("QUERY_STRING", ""))
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length) if length else b""
        headers = _headers_from_environ(environ)

        form: dict[str, list[str]] = {}
        if body and environ.get("CONTENT_TYPE", "").startswith("application/x-www-form-urlencoded"):
            form = parse_qs(body.decode())

        self.requests.append(
            RecordedRequest(
                method=method, path=path, query=query, headers=headers, body=body, form=form
            )
        )

        status, content_type, payload = self._route(
            headers.get("api-key"), path, method, query, form
        )
        start_response(
            f"{status} {HTTPStatus(status).phrase}",
            [("Content-Type", content_type), ("Content-Length", str(len(payload)))],
        )
        return [payload]

    def _route(
        self,
        api_key: str | None,
        path: str,
        method: str,
        query: dict[str, list[str]],
        form: dict[str, list[str]],
    ) -> tuple[int, str, bytes]:
        if api_key in (None, "bad"):
            return 401, "application/json", b'{"message":"unauthorized"}'
        status = _error_status(path)
        if status is not None:
            return status, "application/json", f'{{"message":"error {status}"}}'.encode()
        if method == "DELETE":
            # Real DELETE endpoints answer 200 with an empty body.
            return 200, "application/json", b""
        if _is_binary(path):
            return 200, "application/octet-stream", _BINARY_PAYLOAD
        payload = json.dumps(
            {"method": method, "path": path, "query": query, "form": form}
        ).encode()
        return 200, "application/json", payload

    def __enter__(self) -> LocalAPIServer:
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join()
