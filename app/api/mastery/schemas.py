"""Pydantic schemas for the mastery domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MasteryScoreResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID
    topic: str
    score: float
    last_updated: datetime

    model_config = {"from_attributes": True}
