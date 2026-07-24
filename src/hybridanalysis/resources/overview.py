"""Analysis overview endpoints (``/overview/*``)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class OverviewResource(BaseResource):
    def get(self, sha256: str) -> Any:
        return self._get(f"/overview/{self._seg(sha256)}")

    def summary(self, sha256: str) -> Any:
        return self._get(f"/overview/{self._seg(sha256)}/summary")

    def refresh(self, sha256: str) -> Any:
        return self._get(f"/overview/{self._seg(sha256)}/refresh")

    def sample(self, sha256: str) -> Any:
        return self._get_bytes(f"/overview/{self._seg(sha256)}/sample")
