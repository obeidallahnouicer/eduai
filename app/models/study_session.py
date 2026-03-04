"""StudySession ORM model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cards_reviewed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cards_mastered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="study_sessions"
    )
    course: Mapped["Course"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="study_sessions"
    )
    card_reviews: Mapped[list["CardReview"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="session", cascade="all, delete-orphan"
    )
