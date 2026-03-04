"""FlashcardService — CRUD and AI generation."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content.service import ContentService
from app.api.flashcards.schemas import (
    CreateFlashcardRequest,
    FlashcardResponse,
    UpdateFlashcardRequest,
)
from app.core.exceptions import FlashcardNotFoundError
from app.models.content_source import ContentSource
from app.models.flashcard import Flashcard
from app.services.ai.base import AIClient, FlashcardData
from app.services.storage.base import FileStorage

logger = logging.getLogger(__name__)


class FlashcardService:
    """Handles flashcard CRUD and AI-powered generation."""

    def __init__(
        self, db: AsyncSession, ai: AIClient, storage: FileStorage
    ) -> None:
        self._db = db
        self._ai = ai
        self._storage = storage

    async def create(
        self, data: CreateFlashcardRequest, user_id: UUID
    ) -> FlashcardResponse:
        """Create a single manual flashcard."""
        card = Flashcard(
            course_id=data.course_id,
            created_by=user_id,
            front=data.front,
            back=data.back,
            topic=data.topic,
            difficulty=data.difficulty,
            origin="manual",
        )
        self._db.add(card)
        await self._db.flush()
        return FlashcardResponse.model_validate(card)

    async def generate(
        self, content_source_id: UUID, user_id: UUID
    ) -> list[FlashcardResponse]:
        """Generate flashcards from a content source via the AI client."""
        content_svc = ContentService(self._db, self._storage)
        chunks = await content_svc.get_chunks(content_source_id)
        source = await self._db.get(ContentSource, content_source_id)
        course_title = source.course.title if source and source.course else ""
        cards_data = await self._ai.generate_flashcards(chunks, course_title)
        return await self._persist_generated(cards_data, content_source_id, user_id, source)

    async def list_for_course(self, course_id: UUID) -> list[FlashcardResponse]:
        """Return all non-archived flashcards for a course."""
        result = await self._db.execute(
            select(Flashcard).where(
                Flashcard.course_id == course_id,
                Flashcard.is_archived.is_(False),
            )
        )
        return [FlashcardResponse.model_validate(c) for c in result.scalars().all()]

    async def update(
        self, card_id: UUID, data: UpdateFlashcardRequest
    ) -> FlashcardResponse:
        """Apply non-None patch fields."""
        card = await self._fetch(card_id)
        if data.front is not None:
            card.front = data.front
        if data.back is not None:
            card.back = data.back
        if data.topic is not None:
            card.topic = data.topic
        if data.difficulty is not None:
            card.difficulty = data.difficulty
        if data.is_archived is not None:
            card.is_archived = data.is_archived
        await self._db.flush()
        return FlashcardResponse.model_validate(card)

    async def delete(self, card_id: UUID) -> None:
        """Hard-delete a flashcard."""
        card = await self._fetch(card_id)
        await self._db.delete(card)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch(self, card_id: UUID) -> Flashcard:
        card = await self._db.get(Flashcard, card_id)
        if card is None:
            raise FlashcardNotFoundError(f"Flashcard {card_id} not found")
        return card

    async def _persist_generated(
        self,
        cards_data: list[FlashcardData],
        source_id: UUID,
        user_id: UUID,
        source: object,
    ) -> list[FlashcardResponse]:
        course_id = getattr(source, "course_id", None)
        cards = [
            Flashcard(
                course_id=course_id,
                content_source_id=source_id,
                created_by=user_id,
                front=d.front,
                back=d.back,
                topic=d.topic,
                difficulty=d.difficulty,
                origin="ai",
            )
            for d in cards_data
        ]
        self._db.add_all(cards)
        await self._db.flush()
        return [FlashcardResponse.model_validate(c) for c in cards]
