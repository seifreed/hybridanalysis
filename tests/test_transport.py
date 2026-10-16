"""Tests for the HTTP transport against the real local server."""

from __future__ import annotations

import socket

import httpx
import pytest

from hybridanalysis.config import Config
from hybridanalysis.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)
from hybridanalysis.transport import Transport

from .api_server import VALID_KEY, LocalAPIServer


def test_json_request_returns_parsed_body(transport: Transport) -> None:
    body = transport.request("GET", "/system/version")
    assert body["method"] == "GET"
    assert body["path"] == "/system/version"


def test_text_request(transport: Transport) -> None:
    body = transport.request("GET", "/system/version", parse="text")
    assert isinstance(body, str)
    assert "system/version" in body


def test_bytes_request(transport: Transport) -> None:
    body = transport.request("GET", "/report/abc/sample", parse="bytes")
    assert body == b"BINARY-DATA"


def test_params_and_data_round_trip(transport: Transport, server: LocalAPIServer) -> None:
    body = transport.request(
        "POST", "/search/terms", params={"page": "2"}, data={"filetype": "peexe"}
    )
    assert body["query"] == {"page": ["2"]}
    assert body["form"] == {"filetype": ["peexe"]}
    assert server.requests[-1].method == "POST"


def test_auth_error(server: LocalAPIServer) -> None:
    with (
        Transport(Config(api_key="bad", base_url=server.base_url)) as tr,
        pytest.raises(AuthenticationError) as info,
    ):
        tr.request("GET", "/system/version")
    assert info.value.status_code == 401


def test_not_found_error(transport: Transport) -> None:
    with pytest.raises(NotFoundError):
        transport.request("GET", "/overview/trigger-404")


def test_rate_limit_error(transport: Transport) -> None:
    with pytest.raises(RateLimitError):
        transport.request("GET", "/overview/trigger-429")


def test_generic_api_error(transport: Transport) -> None:
    with pytest.raises(APIError) as info:
        transport.request("GET", "/overview/trigger-500")
    assert info.value.status_code == 500


def test_injected_client_is_not_closed(server: LocalAPIServer) -> None:
    client = httpx.Client(
        base_url=server.base_url, headers={"api-key": VALID_KEY, "User-Agent": "x"}
    )
    transport = Transport(Config(api_key=VALID_KEY, base_url=server.base_url), http_client=client)
    assert transport.request("GET", "/system/version")["path"] == "/system/version"
    transport.close()
    # Injected client stays open and usable because the transport did not own it.
    assert client.get("/system/version").status_code == 200
    client.close()


def test_empty_body_parses_to_none(transport: Transport) -> None:
    assert transport.request("DELETE", "/file-collection/c1") is None


def test_network_error_is_wrapped() -> None:
    # Bind then close an ephemeral port so the connection is refused immediately.
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    closed_port = probe.getsockname()[1]
    probe.close()
    with (
        Transport(Config(api_key="k", base_url=f"http://127.0.0.1:{closed_port}")) as tr,
        pytest.raises(NetworkError, match="failed"),
    ):
        tr.request("GET", "/system/version")


def test_read_timeout_retries_idempotent_request() -> None:
    attempts = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("timed out", request=request)
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    with Transport(Config(api_key="k"), http_client=client) as tr:
        assert tr.request("GET", "/system/version") == {"ok": True}
    client.close()
    assert attempts == 2


def test_read_timeout_does_not_retry_post() -> None:
    attempts = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("timed out", request=request)

    client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    with (
        Transport(Config(api_key="k"), http_client=client) as tr,
        pytest.raises(NetworkError, match="failed"),
    ):
        tr.request("POST", "/submit/file")
    client.close()
    assert attempts == 1


def test_read_timeout_after_retry_is_wrapped() -> None:
    attempts = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("timed out", request=request)

    client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    with (
        Transport(Config(api_key="k"), http_client=client) as tr,
        pytest.raises(NetworkError, match="failed"),
    ):
        tr.request("GET", "/system/version")
    client.close()
    assert attempts == 2


def test_owned_client_is_closed(config: Config) -> None:
    transport = Transport(config)
    transport.request("GET", "/system/version")
    transport.close()
    with pytest.raises(RuntimeError):
        transport.request("GET", "/system/version")
