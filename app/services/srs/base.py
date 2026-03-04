"""Abstract base class for spaced repetition algorithms.

Any SRS algorithm (SM-2, FSRS, Leitner …) must implement this contract.
All implementations must be pure and stateless — no DB or I/O calls.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewResult:
    """Input to the SRS algorithm after a card has been reviewed."""

    ease_factor: float      # Current ease factor (e.g. 2.5)
    interval_days: int      # Current interval in days
    repetitions: int        # How many times reviewed without failing
    rating: int             # 0=again, 1=hard, 2=good, 3=easy


@dataclass(frozen=True)
class ScheduleOutput:
    """Output from the SRS algorithm — the next review schedule."""

    ease_factor: float      # Updated ease factor
    interval_days: int      # Days until next review
    repetitions: int        # Updated repetition count


class SRSAlgorithm(ABC):
    """Contract that every spaced repetition implementation must satisfy."""

    @abstractmethod
    def compute_next_review(self, result: ReviewResult) -> ScheduleOutput:
        """Compute the next review schedule for a card.

        Args:
            result: The current card state plus the user's rating.

        Returns:
            A :class:`ScheduleOutput` with the updated schedule values.
        """
        ...
