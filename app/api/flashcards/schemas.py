"""Pydantic schemas for the flashcards domain."""

from uuid import UUID

from pydantic import BaseModel, Field


class CreateFlashcardRequest(BaseModel):
    course_id: UUID
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)
    topic: str | None = None
    difficulty: int = Field(default=3, ge=1, le=5)


class GenerateFlashcardsRequest(BaseModel):
    content_source_id: UUID


class UpdateFlashcardRequest(BaseModel):
    front: str | None = Field(default=None, min_length=1)
    back: str | None = Field(default=None, min_length=1)
    topic: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    is_archived: bool | None = None


class FlashcardResponse(BaseModel):
    id: UUID
    course_id: UUID
    content_source_id: UUID | None = None
    created_by: UUID
    front: str
    back: str
    topic: str | None = None
    difficulty: int
    origin: str
    is_archived: bool

    model_config = {"from_attributes": True}
