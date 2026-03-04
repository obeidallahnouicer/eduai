"""Sessions router — POST /sessions, WS /sessions/{id}."""

from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.sessions.handler import SessionHandler
from app.api.sessions.schemas import CreateSessionRequest, SessionResponse
from app.api.sessions.service import SessionService
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db)


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_active_user),
    service: SessionService = Depends(_get_service),
) -> SessionResponse:
    """Create a new study session."""
    return await service.create(current_user.id, request.course_id)


@router.websocket("/{session_id}")
async def session_websocket(
    session_id: str,
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> None:
    """WebSocket endpoint — drives the live study loop."""
    service = SessionService(db)
    handler = SessionHandler(websocket, service)
    await handler.run(session_id)
