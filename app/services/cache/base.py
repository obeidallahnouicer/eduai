"""Abstract base class for cache backends.

Swap RedisCache for an in-memory or Memcached implementation without
touching any service that depends on CacheClient.
"""

from abc import ABC, abstractmethod
from typing import Any


class CacheClient(ABC):
    """Contract that every cache implementation must satisfy."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return the cached value for *key*, or None if absent.

        Args:
            key: Cache key string.

        Returns:
            The deserialised value, or None on a cache miss.
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Store *value* under *key* with a TTL.

        Args:
            key: Cache key string.
            value: Serialisable value to store.
            ttl: Time-to-live in seconds.
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Evict the entry at *key* if it exists.

        Args:
            key: Cache key string.
        """
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return True if *key* exists in the cache.

        Args:
            key: Cache key string.
        """
        ...
