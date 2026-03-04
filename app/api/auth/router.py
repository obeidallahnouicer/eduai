"""Auth router — POST /register, POST /login, POST /refresh.

HTTP only: parse request → call AuthService → return response.
No business logic here.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.api.auth.service import AuthService
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(_get_service),
) -> UserResponse:
    """Register a new user account."""
    return await service.register(request)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    """Authenticate and return a JWT token pair."""
    return await service.login(request.email, request.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
    return await service.refresh(request.refresh_token)
