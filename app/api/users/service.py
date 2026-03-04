"""UserService — profile read and update."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.schemas import UpdateUserRequest, UserResponse
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.models.user import User

logger = logging.getLogger(__name__)


class UserService:
    """Handles user profile operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_me(self, user_id: UUID) -> UserResponse:
        """Return the profile for *user_id*."""
        user = await self._fetch(user_id)
        return UserResponse.model_validate(user)

    async def update_me(self, user_id: UUID, data: UpdateUserRequest) -> UserResponse:
        """Apply non-None fields from *data* to the user's profile."""
        user = await self._fetch(user_id)
        if data.email and data.email != user.email:
            await self._assert_email_free(data.email)
            user.email = data.email
        if data.full_name is not None:
            user.full_name = data.full_name
        await self._db.flush()
        return UserResponse.model_validate(user)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch(self, user_id: UUID) -> User:
        user = await self._db.get(User, user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    async def _assert_email_free(self, email: str) -> None:
        result = await self._db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is not None:
            raise UserAlreadyExistsError(f"Email already in use: {email}")
