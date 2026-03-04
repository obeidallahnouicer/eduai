"""Pydantic schemas for the courses domain."""

from uuid import UUID

from pydantic import BaseModel, Field


class CreateCourseRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class UpdateCourseRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_archived: bool | None = None


class CourseResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: str | None
    is_archived: bool

    model_config = {"from_attributes": True}
