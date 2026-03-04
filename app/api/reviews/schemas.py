"""Pydantic schemas for the reviews domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SubmitReviewRequest(BaseModel):
    flashcard_id: UUID
    session_id: UUID
    rating: int = Field(ge=0, le=3)  # 0=again 1=hard 2=good 3=easy
    ease_factor: float = Field(default=2.5, ge=1.3)
    interval_days: int = Field(default=1, ge=1)
    repetitions: int = Field(default=0, ge=0)


class ReviewResponse(BaseModel):
    id: UUID
    flashcard_id: UUID
    user_id: UUID
    session_id: UUID
    result: str
    ease_factor: float
    interval_days: int
    next_review_at: datetime
    reviewed_at: datetime

    model_config = {"from_attributes": True}
