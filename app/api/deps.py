"""Shared FastAPI dependencies injected across all routers."""

import logging
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import InactiveUserError, InvalidTokenError, UserNotFoundError
from app.core.security import jwt_handler
from app.models.user import User

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the Bearer token and return the matching User row."""
    user_id = _decode_token(credentials.credentials)
    return await _load_user(user_id, db)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Extend get_current_user — also asserts the account is active."""
    if not current_user.is_active:
        raise InactiveUserError("Account is deactivated")
    return current_user


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _decode_token(token: str) -> UUID:
    """Wrap jwt_handler so the exception stays a domain exception."""
    try:
        return jwt_handler.decode_access_token(token)
    except InvalidTokenError:
        raise
    except Exception as exc:
        raise InvalidTokenError("Could not validate credentials") from exc


async def _load_user(user_id: UUID, db: AsyncSession) -> User:
    """Fetch user by primary key; raise UserNotFoundError if absent."""
    user = await db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    return user
