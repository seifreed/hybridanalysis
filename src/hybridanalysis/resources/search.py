"""Search endpoints (``/search/*``)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class SearchResource(BaseResource):
    def hash(self, hash_value: str) -> Any:
        """Convert any hash format to SHA256 and return associated reports."""
        return self._get("/search/hash", params={"hash": hash_value})

    def terms(self, **terms: str) -> Any:
        """Search by any Falcon Sandbox terms (e.g. ``domain``, ``host``, ``vx_family``).

        ``verdict`` is numeric (1-5), dates use ``Y-m-d H:i``; see the README for the
        full field list.
        """
        return self._post("/search/terms", data=self._form(**terms))
