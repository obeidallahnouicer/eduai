"""ContentSource ORM model — represents an uploaded PDF or text file."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ContentSource(Base):
    __tablename__ = "content_sources"

    # updated_at is not needed for this append-only table — override to exclude
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)          # pdf | text
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255))
    is_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    course: Mapped["Course"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="content_sources"
    )
    uploader: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        foreign_keys=[uploaded_by]
    )
    flashcards: Mapped[list["Flashcard"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="content_source"
    )
