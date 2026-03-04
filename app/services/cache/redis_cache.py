"""Redis-backed implementation of CacheClient."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.services.cache.base import CacheClient

logger = logging.getLogger(__name__)


class RedisCache(CacheClient):
    """Stores values as JSON in Redis."""

    def __init__(self, client: aioredis.Redis) -> None:  # type: ignore[type-arg]
        self._client = client

    async def get(self, key: str) -> Any | None:
        """Return the deserialised value for *key*, or None on a miss."""
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Serialise *value* to JSON and store it with a TTL."""
        await self._client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        """Remove *key* from Redis."""
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """Return True if *key* exists in Redis."""
        return bool(await self._client.exists(key))
