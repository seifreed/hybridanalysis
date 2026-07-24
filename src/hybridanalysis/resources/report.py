"""Sandbox report endpoints (``/report/*``)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class ReportResource(BaseResource):
    def state(self, report_id: str) -> Any:
        return self._get(f"/report/{self._seg(report_id)}/state")

    def summary(self, report_id: str) -> Any:
        return self._get(f"/report/{self._seg(report_id)}/summary")

    def json_report(self, report_id: str) -> Any:
        return self._get(f"/report/{self._seg(report_id)}/report/json")

    def children(self, report_id: str) -> Any:
        return self._get(f"/report/{self._seg(report_id)}/children")

    def screenshots(self, report_id: str) -> Any:
        return self._get(f"/report/{self._seg(report_id)}/screenshots")

    def memory_dumps_list(self, report_id: str) -> Any:
        return self._get(f"/report/{self._seg(report_id)}/memory-dumps-list")

    def memory_dump_extracted_strings(self, report_id: str, filename: str) -> Any:
        """Return extracted strings for a memory dump (see ``memory_dumps_list``)."""
        return self._get(
            f"/report/{self._seg(report_id)}/memory-dump/extracted-strings",
            params={"filename": filename},
        )

    def memory_strings(self, report_id: str) -> Any:
        return self._get_text(f"/report/{self._seg(report_id)}/memory-strings")

    def memory_dump_hex_dump(self, report_id: str, filename: str) -> Any:
        """Return the hex dump for a memory dump (see ``memory_dumps_list``)."""
        return self._get_text(
            f"/report/{self._seg(report_id)}/memory-dump/hex-dump", params={"filename": filename}
        )

    def sample(self, report_id: str) -> Any:
        return self._get_bytes(f"/report/{self._seg(report_id)}/sample")

    def pcap(self, report_id: str) -> Any:
        return self._get_bytes(f"/report/{self._seg(report_id)}/pcap")

    def certificate(self, report_id: str) -> Any:
        return self._get_bytes(f"/report/{self._seg(report_id)}/certificate")

    def dropped_file(self, report_id: str, file_hash: str) -> Any:
        return self._get_bytes(
            f"/report/{self._seg(report_id)}/dropped-file/{self._seg(file_hash)}"
        )

    def dropped_file_raw(self, report_id: str, file_hash: str) -> Any:
        return self._get_bytes(
            f"/report/{self._seg(report_id)}/dropped-file-raw/{self._seg(file_hash)}"
        )

    def dropped_files(self, report_id: str) -> Any:
        """Download all dropped binaries as a zip archive."""
        return self._get_bytes(f"/report/{self._seg(report_id)}/dropped-files-v2")
