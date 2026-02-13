"""FileStore abstraction for document storage (local filesystem backend)."""

import os
import uuid
from pathlib import Path

from app.config import settings


class FileStore:
    """Store and retrieve uploaded files on the local filesystem."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, filename: str) -> tuple[uuid.UUID, str]:
        """
        Save file content to storage.

        Returns:
            (doc_id, storage_path) tuple
        """
        doc_id = uuid.uuid4()
        ext = os.path.splitext(filename)[1]
        storage_path = self.base_dir / f"{doc_id}{ext}"
        storage_path.write_bytes(content)
        return doc_id, str(storage_path)

    def get(self, storage_path: str) -> bytes:
        """Retrieve file content from storage."""
        path = Path(storage_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        return path.read_bytes()

    def delete(self, storage_path: str) -> None:
        """Delete a file from storage."""
        path = Path(storage_path)
        if path.exists():
            path.unlink()
