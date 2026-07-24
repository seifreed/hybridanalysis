"""The top-level Hybrid Analysis client."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import httpx

from ._lifecycle import SyncCloseable
from .config import Config, load
from .resources import (
    AbuseReportsResource,
    FeedResource,
    FileCollectionResource,
    KeyResource,
    OverviewResource,
    QuickScanResource,
    ReportResource,
    SearchResource,
    SubmitResource,
    SystemResource,
)
from .transport import Transport


class HybridAnalysisClient(SyncCloseable):
    """Client exposing every API tag as a resource attribute.

    Example::

        with HybridAnalysisClient.from_env() as client:
            client.system.version()
    """

    def __init__(self, config: Config, http_client: httpx.Client | None = None) -> None:
        self._transport = Transport(config, http_client)
        self.feed = FeedResource(self._transport)
        self.key = KeyResource(self._transport)
        self.overview = OverviewResource(self._transport)
        self.quick_scan = QuickScanResource(self._transport)
        self.submit = SubmitResource(self._transport)
        self.report = ReportResource(self._transport)
        self.search = SearchResource(self._transport)
        self.file_collection = FileCollectionResource(self._transport)
        self.abuse_reports = AbuseReportsResource(self._transport)
        self.system = SystemResource(self._transport)

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        config_path: Path | None = None,
    ) -> HybridAnalysisClient:
        """Build a client from the ``HYBRIDANALYSIS`` env var or a config file."""
        return cls(load(env=env, config_path=config_path))

    def close(self) -> None:
        self._transport.close()
