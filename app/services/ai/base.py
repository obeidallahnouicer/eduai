"""Abstract base class for all AI clients.

Concrete implementations (e.g. OpenAI, Anthropic) must subclass this.
Services depend on AIClient — never on a concrete implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class FlashcardData:
    """Plain data object returned by the AI layer.

    Deliberately not a SQLAlchemy model — crosses the AI ↔ service boundary.
    """

    front: str
    back: str
    topic: str
    difficulty: int  # 1–5


class AIClient(ABC):
    """Contract that every AI provider implementation must satisfy."""

    @abstractmethod
    async def generate_flashcards(
        self,
        chunks: list[str],
        course_title: str,
    ) -> list[FlashcardData]:
        """Generate flashcards from *chunks* of source text.

        Args:
            chunks: Tokenised segments of the source document.
            course_title: Used to give the model context about the subject.

        Returns:
            A list of :class:`FlashcardData` objects ready for persistence.
        """
        ...
