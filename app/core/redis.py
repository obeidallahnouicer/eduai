"""Redis client factory and FastAPI dependency."""

import logging
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None  # type: ignore[type-arg]


def _make_client() -> aioredis.Redis:  # type: ignore[type-arg]
    return aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


def get_redis_client() -> aioredis.Redis:  # type: ignore[type-arg]
    """Return the singleton Redis client, creating it on first call."""
    global _redis_client
    if _redis_client is None:
        _redis_client = _make_client()
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection — called on app shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[type-arg]
    """Yield the Redis client."""
    yield get_redis_client()
