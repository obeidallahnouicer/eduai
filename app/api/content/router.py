"""Content router — POST /content/upload."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content.schemas import ContentSourceResponse
from app.api.content.service import ContentService
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.services.storage.local_storage import LocalStorage

router = APIRouter(prefix="/content", tags=["content"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ContentService:
    return ContentService(db, LocalStorage())


@router.post(
    "/upload",
    response_model=ContentSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_content(
    course_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    service: ContentService = Depends(_get_service),
) -> ContentSourceResponse:
    """Upload a PDF or text file and attach it to a course."""
    data = await file.read()
    file_type = _resolve_type(file.content_type or "")
    return await service.upload(
        course_id=course_id,
        uploader_id=current_user.id,
        filename=file.filename or "upload",
        file_type=file_type,
        data=data,
    )


def _resolve_type(content_type: str) -> str:
    """Map MIME type to our internal file_type string."""
    if "pdf" in content_type:
        return "pdf"
    return "text"
