"""The async top-level Hybrid Analysis client."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import httpx

from hybridanalysis._lifecycle import AsyncCloseable
from hybridanalysis.config import Config, load

from .resources import (
    AsyncAbuseReportsResource,
    AsyncFeedResource,
    AsyncFileCollectionResource,
    AsyncKeyResource,
    AsyncOverviewResource,
    AsyncQuickScanResource,
    AsyncReportResource,
    AsyncSearchResource,
    AsyncSubmitResource,
    AsyncSystemResource,
)
from .transport import AsyncTransport


class AsyncHybridAnalysisClient(AsyncCloseable):
    """Async client exposing every API tag as a resource attribute.

    Example::

        async with AsyncHybridAnalysisClient.from_env() as client:
            await client.system.version()
    """

    def __init__(self, config: Config, http_client: httpx.AsyncClient | None = None) -> None:
        self._transport = AsyncTransport(config, http_client)
        self.feed = AsyncFeedResource(self._transport)
        self.key = AsyncKeyResource(self._transport)
        self.overview = AsyncOverviewResource(self._transport)
        self.quick_scan = AsyncQuickScanResource(self._transport)
        self.submit = AsyncSubmitResource(self._transport)
        self.report = AsyncReportResource(self._transport)
        self.search = AsyncSearchResource(self._transport)
        self.file_collection = AsyncFileCollectionResource(self._transport)
        self.abuse_reports = AsyncAbuseReportsResource(self._transport)
        self.system = AsyncSystemResource(self._transport)

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        config_path: Path | None = None,
    ) -> AsyncHybridAnalysisClient:
        """Build a client from the ``HYBRIDANALYSIS`` env var or a config file."""
        return cls(load(env=env, config_path=config_path))

    async def aclose(self) -> None:
        await self._transport.aclose()
