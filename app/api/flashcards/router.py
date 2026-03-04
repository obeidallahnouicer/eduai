"""Flashcards router — CRUD + AI generation."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.flashcards.schemas import (
    CreateFlashcardRequest,
    FlashcardResponse,
    GenerateFlashcardsRequest,
    UpdateFlashcardRequest,
)
from app.api.flashcards.service import FlashcardService
from app.core.database import get_db
from app.models.user import User
from app.services.ai.llm_client import LLMClient
from app.services.cache.redis_cache import RedisCache
from app.services.storage.local_storage import LocalStorage

import redis.asyncio as aioredis

from app.core.config import settings

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


def _get_service(db: AsyncSession = Depends(get_db)) -> FlashcardService:
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    cache = RedisCache(redis_client)
    return FlashcardService(db, LLMClient(cache), LocalStorage())


@router.post("", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
async def create_flashcard(
    request: CreateFlashcardRequest,
    current_user: User = Depends(get_current_active_user),
    service: FlashcardService = Depends(_get_service),
) -> FlashcardResponse:
    return await service.create(request, current_user.id)


@router.post(
    "/generate",
    response_model=list[FlashcardResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_flashcards(
    request: GenerateFlashcardsRequest,
    current_user: User = Depends(get_current_active_user),
    service: FlashcardService = Depends(_get_service),
) -> list[FlashcardResponse]:
    return await service.generate(request.content_source_id, current_user.id)


@router.get("", response_model=list[FlashcardResponse])
async def list_flashcards(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: FlashcardService = Depends(_get_service),
) -> list[FlashcardResponse]:
    return await service.list_for_course(course_id)


@router.patch("/{card_id}", response_model=FlashcardResponse)
async def update_flashcard(
    card_id: UUID,
    request: UpdateFlashcardRequest,
    current_user: User = Depends(get_current_active_user),
    service: FlashcardService = Depends(_get_service),
) -> FlashcardResponse:
    return await service.update(card_id, request)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flashcard(
    card_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: FlashcardService = Depends(_get_service),
) -> None:
    await service.delete(card_id)
