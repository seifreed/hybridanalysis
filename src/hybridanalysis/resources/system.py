"""System endpoints (``/system/*``)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class SystemResource(BaseResource):
    def version(self) -> Any:
        return self._get("/system/version")

    def environments(self) -> Any:
        return self._get("/system/environments")

    def action_scripts(self) -> Any:
        return self._get("/system/action-scripts")

    def stats(self) -> Any:
        return self._get("/system/stats")

    def configuration(self) -> Any:
        return self._get("/system/configuration")

    def queue_size(self) -> Any:
        return self._get("/system/queue-size")

    def total_submissions(self) -> Any:
        return self._get("/system/total-submissions")
