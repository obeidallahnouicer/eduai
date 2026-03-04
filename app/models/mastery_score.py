"""MasteryScore ORM model — updated after each study session."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MasteryScore(Base):
    __tablename__ = "mastery_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "topic", name="uq_mastery_user_course_topic"),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_mastery_score_range"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="mastery_scores"
    )
    course: Mapped["Course"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="mastery_scores"
    )
