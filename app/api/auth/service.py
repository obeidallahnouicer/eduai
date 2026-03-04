"""AuthService — registration, login, and token refresh logic."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schemas import RegisterRequest, TokenResponse, UserResponse
from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import hash_password, jwt_handler, verify_password
from app.models.user import User

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration, login, and JWT token lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Create a new user; raise UserAlreadyExistsError if email taken."""
        await self._assert_email_available(data.email)
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        self._db.add(user)
        await self._db.flush()
        logger.info("Registered new user %s", user.id)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        """Validate credentials and return a token pair."""
        user = await self._fetch_by_email(email)
        self._assert_password_valid(password, user.hashed_password)
        self._assert_user_active(user)
        return self._issue_tokens(user.id)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Rotate tokens using a valid refresh token."""
        user_id = self._decode_refresh(refresh_token)
        user = await self._fetch_by_id(user_id)
        self._assert_user_active(user)
        return self._issue_tokens(user.id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _assert_email_available(self, email: str) -> None:
        result = await self._db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is not None:
            raise UserAlreadyExistsError(f"Email already registered: {email}")

    async def _fetch_by_email(self, email: str) -> User:
        result = await self._db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise InvalidCredentialsError("Invalid email or password")
        return user

    async def _fetch_by_id(self, user_id: UUID) -> User:
        user = await self._db.get(User, user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    @staticmethod
    def _assert_password_valid(plain: str, hashed: str) -> None:
        if not verify_password(plain, hashed):
            raise InvalidCredentialsError("Invalid email or password")

    @staticmethod
    def _assert_user_active(user: User) -> None:
        if not user.is_active:
            raise InactiveUserError("Account is deactivated")

    @staticmethod
    def _decode_refresh(token: str) -> UUID:
        try:
            return jwt_handler.decode_refresh_token(token)
        except Exception as exc:
            raise InvalidTokenError("Invalid or expired refresh token") from exc

    @staticmethod
    def _issue_tokens(user_id: UUID) -> TokenResponse:
        return TokenResponse(
            access_token=jwt_handler.create_access_token(user_id),
            refresh_token=jwt_handler.create_refresh_token(user_id),
        )
