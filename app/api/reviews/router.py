"""Reviews router — POST /reviews."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.reviews.schemas import ReviewResponse, SubmitReviewRequest
from app.api.reviews.service import ReviewService
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(db)


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    request: SubmitReviewRequest,
    current_user: User = Depends(get_current_active_user),
    service: ReviewService = Depends(_get_service),
) -> ReviewResponse:
    """Submit a card review result and receive the next SM-2 schedule."""
    return await service.submit(current_user.id, request)
