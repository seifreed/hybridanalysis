"""Quick-scan endpoints (``/quick-scan/*``)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseResource


class QuickScanResource(BaseResource):
    def state(self) -> Any:
        """Return the list of available scanners."""
        return self._get("/quick-scan/state")

    def file(self, file_path: str | Path, scan_type: str, **options: str) -> Any:
        """Submit a file for quick scan."""
        return self._post_file(
            "/quick-scan/file", file_path, data=self._form(scan_type=scan_type, **options)
        )

    def url(self, url: str, scan_type: str, **options: str) -> Any:
        """Submit a URL (or file URL) for quick scan."""
        return self._post(
            "/quick-scan/url", data=self._form(url=url, scan_type=scan_type, **options)
        )

    def get(self, scan_id: str) -> Any:
        """Return quick-scan results."""
        return self._get(f"/quick-scan/{self._seg(scan_id)}")

    def convert_to_full(self, scan_id: str, **options: str) -> Any:
        """Convert a quick scan into a full sandbox report."""
        return self._post(
            f"/quick-scan/{self._seg(scan_id)}/convert-to-full", data=self._form(**options)
        )
