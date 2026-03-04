"""MasteryService — compute and retrieve per-topic mastery scores."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.mastery.schemas import MasteryScoreResponse
from app.models.card_review import CardReview
from app.models.flashcard import Flashcard
from app.models.mastery_score import MasteryScore

logger = logging.getLogger(__name__)

_MASTERY_THRESHOLD = 2   # rating >= this counts as "good"
_MAX_SCORE = 100.0


class MasteryService:
    """Retrieves and recomputes mastery scores for a course."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_for_course(
        self, user_id: UUID, course_id: UUID
    ) -> list[MasteryScoreResponse]:
        """Return all mastery score rows for the given user + course."""
        result = await self._db.execute(
            select(MasteryScore).where(
                MasteryScore.user_id == user_id,
                MasteryScore.course_id == course_id,
            )
        )
        return [MasteryScoreResponse.model_validate(m) for m in result.scalars().all()]

    async def recompute_for_course(
        self, user_id: UUID, course_id: UUID
    ) -> list[MasteryScoreResponse]:
        """Recompute mastery from review history and upsert the rows."""
        topic_scores = await self._compute_topic_scores(user_id, course_id)
        await self._upsert_scores(user_id, course_id, topic_scores)
        return await self.get_for_course(user_id, course_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _compute_topic_scores(
        self, user_id: UUID, course_id: UUID
    ) -> dict[str, float]:
        rows = await self._db.execute(
            select(CardReview, Flashcard)
            .join(Flashcard, CardReview.flashcard_id == Flashcard.id)
            .where(CardReview.user_id == user_id, Flashcard.course_id == course_id)
        )
        topic_totals: dict[str, list[int]] = {}
        for review, card in rows.all():
            topic = card.topic or "General"
            topic_totals.setdefault(topic, [])
            topic_totals[topic].append(1 if review.rating >= _MASTERY_THRESHOLD else 0)  # type: ignore[attr-defined]
        return {t: (sum(v) / len(v)) * _MAX_SCORE for t, v in topic_totals.items()}

    async def _upsert_scores(
        self, user_id: UUID, course_id: UUID, scores: dict[str, float]
    ) -> None:
        for topic, score in scores.items():
            result = await self._db.execute(
                select(MasteryScore).where(
                    MasteryScore.user_id == user_id,
                    MasteryScore.course_id == course_id,
                    MasteryScore.topic == topic,
                )
            )
            row = result.scalar_one_or_none()
            if row:
                row.score = score
                row.last_updated = datetime.now(UTC)
            else:
                self._db.add(MasteryScore(
                    user_id=user_id, course_id=course_id, topic=topic, score=score
                ))
        await self._db.flush()
