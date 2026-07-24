"""Context-manager mixins shared by the transports and clients.

The ``with`` / ``async with`` protocol is identical across the sync pair
(``Transport``, ``HybridAnalysisClient``) and the async pair, so it lives here
once; each class only implements ``close`` / ``aclose``.
"""

from __future__ import annotations

import abc
from types import TracebackType
from typing import Self


class SyncCloseable(abc.ABC):
    """Adds ``with`` support to a class that implements :meth:`close`."""

    @abc.abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class AsyncCloseable(abc.ABC):
    """Adds ``async with`` support to a class that implements :meth:`aclose`."""

    @abc.abstractmethod
    async def aclose(self) -> None: ...

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
