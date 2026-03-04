"""Users router — GET /me, PATCH /me."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.users.schemas import UpdateUserRequest, UserResponse
from app.api.users.service import UserService
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


def _get_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_service),
) -> UserResponse:
    """Return the authenticated user's profile."""
    return await service.get_me(current_user.id)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_service),
) -> UserResponse:
    """Update the authenticated user's profile."""
    return await service.update_me(current_user.id, request)
