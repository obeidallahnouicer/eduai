"""ContentService — upload, parse, and chunk source files."""

import hashlib
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content.chunker import TextChunker
from app.api.content.parser import parse_file
from app.api.content.schemas import ContentSourceResponse
from app.core.config import settings
from app.core.exceptions import ContentSourceNotFoundError, FileTooLargeError
from app.models.content_source import ContentSource
from app.services.storage.base import FileStorage

logger = logging.getLogger(__name__)

_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
_CHUNKER = TextChunker()


class ContentService:
    """Handles file upload, parsing, and chunking."""

    def __init__(self, db: AsyncSession, storage: FileStorage) -> None:
        self._db = db
        self._storage = storage

    async def upload(
        self,
        course_id: UUID,
        uploader_id: UUID,
        filename: str,
        file_type: str,
        data: bytes,
    ) -> ContentSourceResponse:
        """Persist the file and create a ContentSource row."""
        self._assert_size(data)
        content_hash = self._hash(data)
        storage_path = await self._storage.save(filename, data)
        source = ContentSource(
            course_id=course_id,
            uploaded_by=uploader_id,
            type=file_type,
            storage_path=storage_path,
            original_name=filename,
            content_hash=content_hash,
        )
        self._db.add(source)
        await self._db.flush()
        logger.info("Uploaded content source %s", source.id)
        return ContentSourceResponse.model_validate(source)

    async def get_chunks(self, source_id: UUID) -> list[str]:
        """Parse the source file and return text chunks."""
        source = await self._fetch(source_id)
        data = await self._storage.load(source.storage_path)
        text = parse_file(source.type, data)
        chunks = _CHUNKER.chunk(text)
        await self._mark_processed(source)
        return chunks

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch(self, source_id: UUID) -> ContentSource:
        source = await self._db.get(ContentSource, source_id)
        if source is None:
            raise ContentSourceNotFoundError(f"Content source {source_id} not found")
        return source

    async def _mark_processed(self, source: ContentSource) -> None:
        source.is_processed = True
        await self._db.flush()

    @staticmethod
    def _assert_size(data: bytes) -> None:
        if len(data) > _MAX_BYTES:
            raise FileTooLargeError(
                f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit"
            )

    @staticmethod
    def _hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
