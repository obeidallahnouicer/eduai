"""ReviewService — persist card review results with SM-2 scheduling."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.reviews.schemas import ReviewResponse, SubmitReviewRequest
from app.models.card_review import CardReview
from app.services.srs.base import ReviewResult
from app.services.srs.sm2 import SM2Algorithm

logger = logging.getLogger(__name__)

_RATING_LABELS = {0: "again", 1: "hard", 2: "good", 3: "easy"}
_srs = SM2Algorithm()


class ReviewService:
    """Persists a card review and computes the next schedule via SM-2."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def submit(
        self, user_id: UUID, data: SubmitReviewRequest
    ) -> ReviewResponse:
        """Run SM-2, persist the CardReview row, and return it."""
        schedule = _srs.compute_next_review(
            ReviewResult(
                ease_factor=data.ease_factor,
                interval_days=data.interval_days,
                repetitions=data.repetitions,
                rating=data.rating,
            )
        )
        next_review = datetime.now(UTC) + timedelta(days=schedule.interval_days)
        review = CardReview(
            flashcard_id=data.flashcard_id,
            user_id=user_id,
            session_id=data.session_id,
            result=_RATING_LABELS[data.rating],
            ease_factor=schedule.ease_factor,
            interval_days=schedule.interval_days,
            next_review_at=next_review,
            reviewed_at=datetime.now(UTC),
        )
        self._db.add(review)
        await self._db.flush()
        logger.info("Persisted review %s for card %s", review.id, data.flashcard_id)
        return ReviewResponse.model_validate(review)
