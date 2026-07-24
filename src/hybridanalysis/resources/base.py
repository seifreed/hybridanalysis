"""Base class and shared helpers for API resource groups.

The resource classes (``system``, ``report``, ...) define each endpoint exactly
once here. The synchronous helpers below return values directly; the async client
provides an ``AsyncBaseResource`` that overrides these helpers as coroutines, so
the same resource method works for both clients (see ``hybridanalysis.aio``).
Return types are ``Any`` because a shared method must be usable both as a plain
value (sync) and as an awaitable (async).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO, Protocol
from urllib.parse import quote

from hybridanalysis._http import Parse


class SupportsRequest(Protocol):
    """The transport interface the resource layer depends on.

    Defined here (dependency inversion): both the sync ``Transport`` and the async
    ``AsyncTransport`` satisfy it structurally. The return is ``Any`` because the
    sync transport returns a value while the async one returns an awaitable.
    """

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = ...,
        data: dict[str, Any] | None = ...,
        files: dict[str, tuple[str, bytes | BinaryIO]] | None = ...,
        parse: Parse = ...,
    ) -> Any: ...


class BaseResource:
    """Common HTTP helpers shared by every resource group (sync)."""

    def __init__(self, transport: SupportsRequest) -> None:
        self._transport = transport

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._transport.request("GET", path, params=params)

    def _get_bytes(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._transport.request("GET", path, params=params, parse="bytes")

    def _get_text(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._transport.request("GET", path, params=params, parse="text")

    def _post(self, path: str, *, data: dict[str, Any] | None = None) -> Any:
        return self._transport.request("POST", path, data=data)

    def _post_bytes(self, path: str, *, data: dict[str, Any] | None = None) -> Any:
        return self._transport.request("POST", path, data=data, parse="bytes")

    def _post_file(
        self,
        path: str,
        file_path: str | Path,
        *,
        field: str = "file",
        data: dict[str, Any] | None = None,
    ) -> Any:
        source = Path(file_path)
        with source.open("rb") as handle:
            return self._transport.request(
                "POST", path, data=data, files={field: (source.name, handle)}
            )

    def _delete(self, path: str) -> Any:
        return self._transport.request("DELETE", path)

    @staticmethod
    def _form(**fields: str) -> dict[str, str]:
        """Merge a method's required field(s) and extra options into a form body."""
        return dict(fields)

    @staticmethod
    def _seg(value: str) -> str:
        """Percent-encode a caller value for safe use as one URL path segment.

        Prevents an id/hash containing ``/``, ``?`` or ``#`` from altering which
        endpoint is called (``:`` is kept — it is a valid path char used by the
        ``sha256:environmentId`` id format).
        """
        return quote(value, safe=":")
