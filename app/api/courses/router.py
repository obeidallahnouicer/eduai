"""Courses router — full CRUD under /courses."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.courses.schemas import (
    CourseResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from app.api.courses.service import CourseService
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/courses", tags=["courses"])


def _get_service(db: AsyncSession = Depends(get_db)) -> CourseService:
    return CourseService(db)


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    request: CreateCourseRequest,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(_get_service),
) -> CourseResponse:
    return await service.create(request, current_user.id)


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(_get_service),
) -> list[CourseResponse]:
    return await service.list_for_user(current_user.id)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(_get_service),
) -> CourseResponse:
    return await service.get(course_id, current_user.id)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    request: UpdateCourseRequest,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(_get_service),
) -> CourseResponse:
    return await service.update(course_id, current_user.id, request)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(_get_service),
) -> None:
    await service.delete(course_id, current_user.id)
