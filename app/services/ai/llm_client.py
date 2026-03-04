"""NVIDIA NIM LLM client — concrete AIClient implementation.

Uses the OpenAI-compatible SDK pointing at the NVIDIA NIM endpoint.
Responses are cached in Redis to avoid redundant API calls.
"""

import hashlib
import json
import logging
from dataclasses import asdict

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import FlashcardGenerationError
from app.services.ai.base import AIClient, FlashcardData
from app.services.ai.prompts import SYSTEM_FLASHCARD_GENERATION, USER_FLASHCARD_GENERATION
from app.services.cache.base import CacheClient

logger = logging.getLogger(__name__)


class LLMClient(AIClient):
    """Calls NVIDIA NIM (openai/gpt-oss-120b) to generate flashcards."""

    def __init__(self, cache: CacheClient) -> None:
        self._cache = cache
        self._client = AsyncOpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url=str(settings.OPENAI_BASE_URL),
        )

    async def generate_flashcards(
        self, chunks: list[str], course_title: str
    ) -> list[FlashcardData]:
        """Return cached flashcards or call the LLM and cache the result."""
        cache_key = self._build_cache_key(chunks, course_title)
        cached = await self._cache.get(cache_key)
        if cached:
            return [FlashcardData(**item) for item in cached]
        cards = await self._call_llm(chunks, course_title)
        await self._cache.set(cache_key, [asdict(c) for c in cards], ttl=settings.AI_CACHE_TTL_SECONDS)
        return cards

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, chunks: list[str], course_title: str) -> list[FlashcardData]:
        """Stream the LLM response and parse it into FlashcardData objects."""
        prompt = USER_FLASHCARD_GENERATION.format(
            course_title=course_title,
            chunks="\n\n---\n\n".join(chunks[: settings.AI_MAX_CHUNKS_PER_REQUEST]),
        )
        raw = await self._stream_response(prompt)
        return self._parse_response(raw)

    async def _stream_response(self, user_prompt: str) -> str:
        """Accumulate the streamed response into a single string."""
        stream = await self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_FLASHCARD_GENERATION},
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.AI_TEMPERATURE,
            top_p=settings.AI_TOP_P,
            max_tokens=settings.AI_MAX_TOKENS,
            stream=True,
        )
        parts: list[str] = []
        async for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None):
                parts.append(delta.content)
        return "".join(parts)

    @staticmethod
    def _parse_response(raw: str) -> list[FlashcardData]:
        """Parse the JSON array from the LLM response."""
        try:
            items: list[dict] = json.loads(raw)  # type: ignore[type-arg]
            return [FlashcardData(**item) for item in items]
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.error("Failed to parse LLM response: %s", exc)
            raise FlashcardGenerationError("LLM returned invalid JSON") from exc

    @staticmethod
    def _build_cache_key(chunks: list[str], course_title: str) -> str:
        """Deterministic SHA-256 cache key from content + title."""
        content = course_title + "".join(chunks)
        digest = hashlib.sha256(content.encode()).hexdigest()
        return f"flashcards:{digest}"
