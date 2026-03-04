"""Mastery router — GET /mastery/{course_id}."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.mastery.schemas import MasteryScoreResponse
from app.api.mastery.service import MasteryService
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/mastery", tags=["mastery"])


def _get_service(db: AsyncSession = Depends(get_db)) -> MasteryService:
    return MasteryService(db)


@router.get("/{course_id}", response_model=list[MasteryScoreResponse])
async def get_mastery(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: MasteryService = Depends(_get_service),
) -> list[MasteryScoreResponse]:
    """Return mastery scores for the authenticated user in a course."""
    return await service.get_for_course(current_user.id, course_id)


@router.post("/{course_id}/recompute", response_model=list[MasteryScoreResponse])
async def recompute_mastery(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: MasteryService = Depends(_get_service),
) -> list[MasteryScoreResponse]:
    """Recompute and return updated mastery scores from review history."""
    return await service.recompute_for_course(current_user.id, course_id)
