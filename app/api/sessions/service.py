"""SessionService — create sessions and manage the card queue."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.sessions.schemas import SessionResponse
from app.core.config import settings
from app.core.exceptions import SessionAlreadyCompletedError, SessionNotFoundError
from app.models.flashcard import Flashcard
from app.models.study_session import StudySession

logger = logging.getLogger(__name__)


class SessionService:
    """Handles study session lifecycle and card queue management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, user_id: UUID, course_id: UUID) -> SessionResponse:
        """Open a new study session."""
        session = StudySession(
            user_id=user_id,
            course_id=course_id,
            started_at=datetime.now(UTC),
        )
        self._db.add(session)
        await self._db.flush()
        logger.info("Created session %s for user %s", session.id, user_id)
        return SessionResponse.model_validate(session)

    async def get_due_cards(self, session_id: UUID) -> list[Flashcard]:
        """Return up to MAX_CARDS_PER_SESSION cards due for review."""
        session = await self._fetch(session_id)
        self._assert_open(session)
        result = await self._db.execute(
            select(Flashcard)
            .where(
                Flashcard.course_id == session.course_id,
                Flashcard.is_archived.is_(False),
            )
            .limit(settings.MAX_CARDS_PER_SESSION)
        )
        return list(result.scalars().all())

    async def close(self, session_id: UUID, mastered: int) -> SessionResponse:
        """Mark the session as ended."""
        session = await self._fetch(session_id)
        session.ended_at = datetime.now(UTC)
        session.cards_mastered = mastered
        await self._db.flush()
        return SessionResponse.model_validate(session)

    async def increment_reviewed(self, session_id: UUID) -> None:
        """Increment the cards_reviewed counter by one."""
        session = await self._fetch(session_id)
        session.cards_reviewed += 1
        await self._db.flush()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch(self, session_id: UUID) -> StudySession:
        session = await self._db.get(StudySession, session_id)
        if session is None:
            raise SessionNotFoundError(f"Session {session_id} not found")
        return session

    @staticmethod
    def _assert_open(session: StudySession) -> None:
        if session.ended_at is not None:
            raise SessionAlreadyCompletedError("Session is already completed")
