"""JWT handling, password hashing, and verification."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Password helpers (module-level, not wrapped in a class — single concern)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT handler
# ---------------------------------------------------------------------------

class JWTHandler:
    """Creates and decodes signed JWT tokens."""

    _ACCESS_TYPE = "access"
    _REFRESH_TYPE = "refresh"

    def create_access_token(self, subject: UUID) -> str:
        """Return a signed access token for *subject*."""
        expires = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        return self._encode(str(subject), self._ACCESS_TYPE, expires)

    def create_refresh_token(self, subject: UUID) -> str:
        """Return a signed refresh token for *subject*."""
        expires = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        return self._encode(str(subject), self._REFRESH_TYPE, expires)

    def decode_access_token(self, token: str) -> UUID:
        """Decode an access token; raise InvalidTokenError on failure."""
        return self._decode(token, self._ACCESS_TYPE)

    def decode_refresh_token(self, token: str) -> UUID:
        """Decode a refresh token; raise InvalidTokenError on failure."""
        return self._decode(token, self._REFRESH_TYPE)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _encode(self, subject: str, token_type: str, expires: datetime) -> str:
        payload = {"sub": subject, "type": token_type, "exp": expires}
        return jwt.encode(
            payload, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def _decode(self, token: str, expected_type: str) -> UUID:
        claims = self._verified_claims(token)
        self._assert_token_type(claims, expected_type)
        return UUID(claims["sub"])

    def _verified_claims(self, token: str) -> dict:  # type: ignore[type-arg]
        try:
            return jwt.decode(
                token,
                settings.APP_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError as exc:
            logger.debug("JWT decode failed: %s", exc)
            raise InvalidTokenError("Token is invalid or expired") from exc

    @staticmethod
    def _assert_token_type(claims: dict, expected: str) -> None:  # type: ignore[type-arg]
        if claims.get("type") != expected:
            raise InvalidTokenError(f"Expected {expected} token")


jwt_handler = JWTHandler()
