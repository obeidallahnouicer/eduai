"""CardReview ORM model — one row per card-per-review event."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CardReview(Base):
    __tablename__ = "card_reviews"

    flashcard_id: Mapped[UUID] = mapped_column(
        ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False
    )
    result: Mapped[str] = mapped_column(
        String(10), nullable=False             # again | hard | good | easy
    )
    ease_factor: Mapped[float] = mapped_column(
        Numeric(4, 2), nullable=False, default=2.5
    )
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    flashcard: Mapped["Flashcard"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="card_reviews"
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="card_reviews"
    )
    session: Mapped["StudySession"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="card_reviews"
    )
