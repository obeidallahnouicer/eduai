"""Local filesystem implementation of FileStorage.

Stores files under settings.UPLOAD_DIR.
Swap this class for an S3Storage later without changing any service.
"""

import logging
from pathlib import Path

import aiofiles

from app.core.config import settings
from app.core.exceptions import ContentProcessingError
from app.services.storage.base import FileStorage

logger = logging.getLogger(__name__)


class LocalStorage(FileStorage):
    """Saves files to the local UPLOAD_DIR directory."""

    def __init__(self) -> None:
        self._base = Path(settings.UPLOAD_DIR)
        self._base.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, data: bytes) -> str:
        """Write *data* to disk and return the relative storage path."""
        dest = self._base / filename
        try:
            async with aiofiles.open(dest, "wb") as fh:
                await fh.write(data)
        except OSError as exc:
            logger.error("Failed to save file %s: %s", filename, exc)
            raise ContentProcessingError(f"Could not save file: {filename}") from exc
        return str(dest)

    async def load(self, path: str) -> bytes:
        """Read and return raw bytes from *path*."""
        try:
            async with aiofiles.open(path, "rb") as fh:
                return await fh.read()
        except OSError as exc:
            logger.error("Failed to load file %s: %s", path, exc)
            raise ContentProcessingError(f"Could not read file: {path}") from exc

    async def delete(self, path: str) -> None:
        """Remove the file at *path* if it exists."""
        target = Path(path)
        if target.exists():
            target.unlink()

    async def exists(self, path: str) -> bool:
        """Return True if *path* exists on disk."""
        return Path(path).exists()
