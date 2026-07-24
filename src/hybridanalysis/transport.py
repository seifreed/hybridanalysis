"""Synchronous HTTP transport wrapping :class:`httpx.Client`."""

from __future__ import annotations

from typing import Any, BinaryIO

import httpx

from ._http import Parse, client_kwargs, parse_response
from ._lifecycle import SyncCloseable
from .config import Config
from .errors import NetworkError


class Transport(SyncCloseable):
    """Thin wrapper over an ``httpx.Client`` that adds auth and error mapping.

    An ``httpx.Client`` may be injected (``http_client``); otherwise one is built
    from ``config``. Ownership follows creation: an injected client is not closed
    by :meth:`close`.
    """

    def __init__(self, config: Config, http_client: httpx.Client | None = None) -> None:
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(**client_kwargs(config))

    def request(
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
            response = self._client.request(method, path, params=params, data=data, files=files)
        except httpx.HTTPError as exc:
            raise NetworkError(f"Request to {path} failed: {exc}") from exc
        return parse_response(response, parse)

    def close(self) -> None:
        """Close the underlying client if this transport created it."""
        if self._owns_client:
            self._client.close()
