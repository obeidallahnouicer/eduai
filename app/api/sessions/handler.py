"""WebSocket session event handler."""

import json
import logging

from fastapi import WebSocket

from app.api.sessions.schemas import WSCardEvent, WSReviewEvent
from app.api.sessions.service import SessionService
from app.services.srs.sm2 import SM2Algorithm
from app.services.srs.base import ReviewResult

logger = logging.getLogger(__name__)

_srs = SM2Algorithm()


class SessionHandler:
    """Drives the WebSocket study loop for a single session."""

    def __init__(self, websocket: WebSocket, service: SessionService) -> None:
        self._ws = websocket
        self._service = service

    async def run(self, session_id: str) -> None:
        """Accept the WebSocket and process review events until the session ends."""
        from uuid import UUID
        await self._ws.accept()
        sid = UUID(session_id)
        cards = await self._service.get_due_cards(sid)
        mastered = 0
        for card in cards:
            await self._send_card(card)
            event = await self._receive_event()
            if event is None:
                break
            mastered += self._process_review(event)
            await self._service.increment_reviewed(sid)
        await self._service.close(sid, mastered)
        await self._ws.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _send_card(self, card: object) -> None:
        event = WSCardEvent(
            flashcard_id=getattr(card, "id"),
            front=getattr(card, "front"),
            back=getattr(card, "back"),
            topic=getattr(card, "topic", None),
        )
        await self._ws.send_text(event.model_dump_json())

    async def _receive_event(self) -> WSReviewEvent | None:
        try:
            raw = await self._ws.receive_text()
            return WSReviewEvent.model_validate(json.loads(raw))
        except Exception as exc:
            logger.warning("WebSocket receive error: %s", exc)
            return None

    @staticmethod
    def _process_review(event: WSReviewEvent) -> int:
        result = ReviewResult(
            ease_factor=2.5, interval_days=1, repetitions=0, rating=event.rating
        )
        _srs.compute_next_review(result)
        return 1 if event.rating >= 2 else 0
