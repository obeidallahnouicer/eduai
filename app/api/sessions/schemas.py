"""Pydantic schemas for the sessions domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    course_id: UUID


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    cards_reviewed: int
    cards_mastered: int

    model_config = {"from_attributes": True}


class WSReviewEvent(BaseModel):
    """Incoming WebSocket message — user submits a card review."""
    flashcard_id: UUID
    rating: int  # 0=again, 1=hard, 2=good, 3=easy


class WSCardEvent(BaseModel):
    """Outgoing WebSocket message — next card to review."""
    flashcard_id: UUID
    front: str
    back: str
    topic: str | None = None
