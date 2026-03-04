"""Pydantic schemas for the content domain."""

from uuid import UUID

from pydantic import BaseModel


class ContentSourceResponse(BaseModel):
    id: UUID
    course_id: UUID
    uploaded_by: UUID
    type: str
    original_name: str | None = None
    is_processed: bool
    content_hash: str | None = None

    model_config = {"from_attributes": True}
