"""Flashcard ORM model."""

from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Flashcard(Base):
    __tablename__ = "flashcards"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_flashcard_difficulty"),
    )

    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_sources.id", ondelete="SET NULL")
    )
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255))
    difficulty: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    origin: Mapped[str] = mapped_column(String(20), nullable=False, default="ai")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    course: Mapped["Course"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="flashcards"
    )
    content_source: Mapped["ContentSource | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="flashcards"
    )
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        foreign_keys=[created_by]
    )
    card_reviews: Mapped[list["CardReview"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="flashcard", cascade="all, delete-orphan"
    )
