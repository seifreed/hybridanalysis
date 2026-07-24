"""API key endpoints (``/key/*``)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class KeyResource(BaseResource):
    def current(self) -> Any:
        return self._get("/key/current")

    def submission_quota(self) -> Any:
        return self._get("/key/submission-quota")
