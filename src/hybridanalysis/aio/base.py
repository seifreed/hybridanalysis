"""Async base resource: overrides the sync helpers as coroutines.

Resource classes are defined once in ``hybridanalysis.resources`` and mixed with
this base (see ``aio.resources``). Because these overrides are coroutines, a
shared resource method such as ``def version(self): return self._get(...)`` returns
an awaitable when the instance uses an :class:`AsyncTransport`.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from hybridanalysis.resources.base import BaseResource


class AsyncBaseResource(BaseResource):
    """Async override of :class:`BaseResource`'s HTTP helpers."""

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._transport.request("GET", path, params=params)

    async def _get_bytes(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._transport.request("GET", path, params=params, parse="bytes")

    async def _get_text(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._transport.request("GET", path, params=params, parse="text")

    async def _post(self, path: str, *, data: dict[str, Any] | None = None) -> Any:
        return await self._transport.request("POST", path, data=data)

    async def _post_bytes(self, path: str, *, data: dict[str, Any] | None = None) -> Any:
        return await self._transport.request("POST", path, data=data, parse="bytes")

    async def _post_file(
        self,
        path: str,
        file_path: str | Path,
        *,
        field: str = "file",
        data: dict[str, Any] | None = None,
    ) -> Any:
        source = Path(file_path)
        # Read off the event loop: opening/reading a file is blocking I/O.
        content = await asyncio.to_thread(source.read_bytes)
        return await self._transport.request(
            "POST", path, data=data, files={field: (source.name, content)}
        )

    async def _delete(self, path: str) -> Any:
        return await self._transport.request("DELETE", path)
