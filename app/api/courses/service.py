"""CourseService — full CRUD for courses."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.courses.schemas import (
    CourseResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from app.core.exceptions import CourseAccessDeniedError, CourseNotFoundError
from app.models.course import Course

logger = logging.getLogger(__name__)


class CourseService:
    """Handles course creation, retrieval, update, and deletion."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, data: CreateCourseRequest, owner_id: UUID) -> CourseResponse:
        """Create a new course owned by *owner_id*."""
        course = Course(owner_id=owner_id, title=data.title, description=data.description)
        self._db.add(course)
        await self._db.flush()
        logger.info("Created course %s for user %s", course.id, owner_id)
        return CourseResponse.model_validate(course)

    async def list_for_user(self, owner_id: UUID) -> list[CourseResponse]:
        """Return all non-archived courses owned by *owner_id*."""
        result = await self._db.execute(
            select(Course).where(Course.owner_id == owner_id, Course.is_archived.is_(False))
        )
        return [CourseResponse.model_validate(c) for c in result.scalars().all()]

    async def get(self, course_id: UUID, owner_id: UUID) -> CourseResponse:
        """Return a single course; raise if not found or not owned."""
        course = await self._fetch_owned(course_id, owner_id)
        return CourseResponse.model_validate(course)

    async def update(
        self, course_id: UUID, owner_id: UUID, data: UpdateCourseRequest
    ) -> CourseResponse:
        """Apply non-None fields to the course."""
        course = await self._fetch_owned(course_id, owner_id)
        if data.title is not None:
            course.title = data.title
        if data.description is not None:
            course.description = data.description
        if data.is_archived is not None:
            course.is_archived = data.is_archived
        await self._db.flush()
        return CourseResponse.model_validate(course)

    async def delete(self, course_id: UUID, owner_id: UUID) -> None:
        """Hard-delete the course."""
        course = await self._fetch_owned(course_id, owner_id)
        await self._db.delete(course)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_owned(self, course_id: UUID, owner_id: UUID) -> Course:
        course = await self._db.get(Course, course_id)
        if course is None:
            raise CourseNotFoundError(f"Course {course_id} not found")
        if course.owner_id != owner_id:
            raise CourseAccessDeniedError("You do not own this course")
        return course
