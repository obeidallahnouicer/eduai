"""Abstract base class for file storage backends.

Swap LocalStorage for S3Storage or GCS without touching any service.
"""

from abc import ABC, abstractmethod


class FileStorage(ABC):
    """Contract that every file storage backend must satisfy."""

    @abstractmethod
    async def save(self, filename: str, data: bytes) -> str:
        """Persist *data* under *filename* and return the storage path.

        Args:
            filename: The original or sanitised file name.
            data: Raw file bytes.

        Returns:
            An opaque storage path that can be passed to :meth:`load`
            or :meth:`delete` later.
        """
        ...

    @abstractmethod
    async def load(self, path: str) -> bytes:
        """Load and return the raw bytes stored at *path*.

        Args:
            path: The storage path returned by :meth:`save`.

        Returns:
            The raw file bytes.
        """
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Remove the file at *path* from the storage backend.

        Args:
            path: The storage path returned by :meth:`save`.
        """
        ...

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Return True if a file exists at *path*.

        Args:
            path: The storage path returned by :meth:`save`.
        """
        ...
