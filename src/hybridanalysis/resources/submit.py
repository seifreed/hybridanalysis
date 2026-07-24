"""Sandbox submission endpoints (``/submit/*``)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseResource


class SubmitResource(BaseResource):
    def file(self, file_path: str | Path, **options: str) -> Any:
        """Submit a file for full sandbox analysis (e.g. ``environment_id``)."""
        return self._post_file("/submit/file", file_path, data=self._form(**options))

    def url(self, url: str, **options: str) -> Any:
        """Submit a URL (or URL with file) for analysis."""
        return self._post("/submit/url", data=self._form(url=url, **options))

    def hash_for_url(self, url: str, **options: str) -> Any:
        """Determine the SHA256 for an online file/URL submission."""
        return self._post("/submit/hash-for-url", data=self._form(url=url, **options))

    def dropped_file(self, report_id: str, file_hash: str, **options: str) -> Any:
        """Resubmit a dropped file (by SHA256) from a parent report for analysis."""
        return self._post(
            "/submit/dropped-file",
            data=self._form(id=report_id, file_hash=file_hash, **options),
        )
