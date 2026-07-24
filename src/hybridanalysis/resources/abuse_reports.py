"""Report deletion endpoints (``/abuse-reports/*``)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class AbuseReportsResource(BaseResource):
    def new(self, sha256: str, reason: str, **options: str) -> Any:
        """Request deletion of a report by ``sha256`` with a ``reason``."""
        return self._post(
            "/abuse-reports/new", data=self._form(sha256=sha256, reason=reason, **options)
        )

    def feed(self) -> Any:
        """Return hashes of removed samples."""
        return self._get("/abuse-reports/feed")
