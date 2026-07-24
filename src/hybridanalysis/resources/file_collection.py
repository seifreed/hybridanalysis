"""File collection endpoints (``/file-collection/*``)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseResource


class FileCollectionResource(BaseResource):
    def create(self, **fields: str) -> Any:
        """Create a collection (optional fields: ``collection_name``, ``comment``)."""
        return self._post("/file-collection/create", data=self._form(**fields))

    def search(self, **fields: str) -> Any:
        """Search collections (fields: ``collection_name``, ``tag``)."""
        return self._post("/file-collection/search", data=self._form(**fields))

    def get(self, collection_id: str) -> Any:
        return self._get(f"/file-collection/{self._seg(collection_id)}")

    def delete(self, collection_id: str) -> Any:
        return self._delete(f"/file-collection/{self._seg(collection_id)}")

    def add_file(self, collection_id: str, file_path: str | Path, **options: str) -> Any:
        """Upload a file to the collection (the API quick-scans it on add)."""
        return self._post_file(
            f"/file-collection/{self._seg(collection_id)}/files/add",
            file_path,
            data=self._form(**options),
        )

    def remove_file(self, collection_id: str, file_hash: str) -> Any:
        return self._delete(
            f"/file-collection/{self._seg(collection_id)}/files/{self._seg(file_hash)}"
        )

    def download(self, collection_id: str) -> Any:
        """Download all collection samples."""
        return self._get_bytes(f"/file-collection/{self._seg(collection_id)}/files/download")

    def download_selected(self, collection_id: str, hashes: list[str]) -> Any:
        """Download selected collection samples by their SHA256 hashes."""
        return self._post_bytes(
            f"/file-collection/{self._seg(collection_id)}/files/download", data={"hashes[]": hashes}
        )
