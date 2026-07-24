"""Tests for the async client and transport, against the real local server."""

from __future__ import annotations

import asyncio
import socket
from collections.abc import Coroutine
from pathlib import Path
from typing import Any

import httpx
import pytest

from hybridanalysis.aio import AsyncHybridAnalysisClient, AsyncTransport
from hybridanalysis.config import Config
from hybridanalysis.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)

from .api_server import VALID_KEY, LocalAPIServer


def run[T](coro: Coroutine[Any, Any, T]) -> T:
    """Execute a coroutine to completion (no pytest-asyncio dependency)."""
    return asyncio.run(coro)


def test_async_transport_parses(config: Config) -> None:
    async def body() -> None:
        async with AsyncTransport(config) as tr:
            js = await tr.request("GET", "/system/version")
            assert js["path"] == "/system/version"
            text = await tr.request("GET", "/system/version", parse="text")
            assert "system/version" in text
            data = await tr.request("GET", "/report/x/sample", parse="bytes")
            assert data == b"BINARY-DATA"
            empty = await tr.request("DELETE", "/file-collection/c1")
            assert empty is None

    run(body())


def test_async_transport_round_trip(config: Config, server: LocalAPIServer) -> None:
    async def body() -> None:
        async with AsyncTransport(config) as tr:
            js = await tr.request(
                "POST", "/search/terms", params={"page": "1"}, data={"filetype": "peexe"}
            )
            assert js["query"] == {"page": ["1"]}
            assert js["form"] == {"filetype": ["peexe"]}
            assert server.requests[-1].method == "POST"

    run(body())


def test_async_transport_errors(server: LocalAPIServer, config: Config) -> None:
    async def body() -> None:
        async with AsyncTransport(Config(api_key="bad", base_url=server.base_url)) as bad:
            with pytest.raises(AuthenticationError):
                await bad.request("GET", "/system/version")
        async with AsyncTransport(config) as tr:
            with pytest.raises(NotFoundError):
                await tr.request("GET", "/overview/trigger-404")
            with pytest.raises(RateLimitError):
                await tr.request("GET", "/overview/trigger-429")
            with pytest.raises(APIError) as info:
                await tr.request("GET", "/overview/trigger-500")
            assert info.value.status_code == 500

    run(body())


def test_async_transport_network_error() -> None:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    closed_port = probe.getsockname()[1]
    probe.close()

    async def body() -> None:
        async with AsyncTransport(
            Config(api_key="k", base_url=f"http://127.0.0.1:{closed_port}")
        ) as tr:
            with pytest.raises(NetworkError, match="failed"):
                await tr.request("GET", "/system/version")

    run(body())


def test_async_injected_client_not_closed(server: LocalAPIServer) -> None:
    async def body() -> None:
        client = httpx.AsyncClient(
            base_url=server.base_url, headers={"api-key": VALID_KEY, "User-Agent": "x"}
        )
        transport = AsyncTransport(
            Config(api_key=VALID_KEY, base_url=server.base_url), http_client=client
        )
        assert (await transport.request("GET", "/system/version"))["path"] == "/system/version"
        await transport.aclose()
        # Not owned, so still usable.
        assert (await client.get("/system/version")).status_code == 200
        await client.aclose()

    run(body())


def test_async_owned_client_closed(config: Config) -> None:
    async def body() -> None:
        transport = AsyncTransport(config)
        await transport.request("GET", "/system/version")
        await transport.aclose()
        with pytest.raises(RuntimeError):
            await transport.request("GET", "/system/version")

    run(body())


def test_async_client_covers_all_helpers(
    config: Config, server: LocalAPIServer, tmp_path: Path
) -> None:
    upload = tmp_path / "s.bin"
    upload.write_bytes(b"data")

    async def body() -> None:
        async with AsyncHybridAnalysisClient(config) as client:
            assert (await client.system.version())["path"] == "/system/version"  # _get
            assert await client.report.sample("job1") == b"BINARY-DATA"  # _get_bytes
            assert "memory-strings" in await client.report.memory_strings("job1")  # _get_text
            assert (await client.search.terms(tag="x"))["form"] == {"tag": ["x"]}  # _post
            selected = await client.file_collection.download_selected("c1", ["h1"])  # _post_bytes
            assert selected == b"BINARY-DATA"
            assert await client.file_collection.delete("c1") is None  # _delete
            uploaded = await client.submit.file(upload, environment_id="160")  # _post_file
            assert uploaded["path"] == "/submit/file"
            assert b"s.bin" in server.requests[-1].body

    run(body())


def test_async_from_env(server: LocalAPIServer) -> None:
    env = {"HYBRIDANALYSIS": VALID_KEY, "HYBRIDANALYSIS_URL": server.base_url}

    async def body() -> None:
        client = AsyncHybridAnalysisClient.from_env(env=env)
        try:
            assert (await client.system.version())["path"] == "/system/version"
        finally:
            await client.aclose()

    run(body())
