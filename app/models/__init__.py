"""Import all models so Alembic and SQLAlchemy can discover them."""

from app.models.base import Base
from app.models.card_review import CardReview
from app.models.content_source import ContentSource
from app.models.course import Course
from app.models.flashcard import Flashcard
from app.models.mastery_score import MasteryScore
from app.models.study_session import StudySession
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Course",
    "ContentSource",
    "Flashcard",
    "StudySession",
    "CardReview",
    "MasteryScore",
]
