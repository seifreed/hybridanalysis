"""Async HTTP transport wrapping :class:`httpx.AsyncClient`."""

from __future__ import annotations

from typing import Any, BinaryIO

import httpx

from hybridanalysis._http import Parse, client_kwargs, parse_response
from hybridanalysis._lifecycle import AsyncCloseable
from hybridanalysis.config import Config
from hybridanalysis.errors import NetworkError


class AsyncTransport(AsyncCloseable):
    """Async counterpart of :class:`hybridanalysis.transport.Transport`.

    An ``httpx.AsyncClient`` may be injected; otherwise one is built from
    ``config``. An injected client is not closed by :meth:`aclose`.
    """

    def __init__(self, config: Config, http_client: httpx.AsyncClient | None = None) -> None:
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(**client_kwargs(config))

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes | BinaryIO]] | None = None,
        parse: Parse = "json",
    ) -> Any:
        """Send a request and return the parsed body, raising on error status."""
        try:
            response = await self._client.request(
                method, path, params=params, data=data, files=files
            )
        except httpx.HTTPError as exc:
            raise NetworkError(f"Request to {path} failed: {exc}") from exc
        return parse_response(response, parse)

    async def aclose(self) -> None:
        """Close the underlying client if this transport created it."""
        if self._owns_client:
            await self._client.aclose()
