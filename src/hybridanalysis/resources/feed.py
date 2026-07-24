"""Feed endpoints (``/feed/*``)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class FeedResource(BaseResource):
    def detonation(self) -> Any:
        return self._get("/feed/detonation")

    def quick_scan(self) -> Any:
        return self._get("/feed/quick-scan")
