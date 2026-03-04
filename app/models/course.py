"""Course ORM model."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

_CASCADE = "all, delete-orphan"


class Course(Base):
    __tablename__ = "courses"

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    owner: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="courses"
    )
    content_sources: Mapped[list["ContentSource"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="course", cascade=_CASCADE
    )
    flashcards: Mapped[list["Flashcard"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="course", cascade=_CASCADE
    )
    study_sessions: Mapped[list["StudySession"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="course", cascade=_CASCADE
    )
    mastery_scores: Mapped[list["MasteryScore"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="course", cascade=_CASCADE
    )
