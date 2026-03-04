"""SM-2 spaced repetition algorithm — pure stateless implementation.

Reference: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
Rating scale: 0=again, 1=hard, 2=good, 3=easy
"""

from app.core.config import settings
from app.services.srs.base import ReviewResult, ScheduleOutput, SRSAlgorithm

# Rating thresholds
_RATING_AGAIN = 0
_RATING_HARD = 1
_RATING_GOOD = 2

# Ease factor deltas per rating
_EF_DELTA = {0: -0.20, 1: -0.15, 2: 0.0, 3: 0.10}

# Interval caps (days)
_FIRST_INTERVAL = 1
_SECOND_INTERVAL = 6


class SM2Algorithm(SRSAlgorithm):
    """SM-2 algorithm.  Stateless — all state lives in CardReview rows."""

    def compute_next_review(self, result: ReviewResult) -> ScheduleOutput:
        """Return the next schedule given *result*."""
        new_ef = self._updated_ease_factor(result.ease_factor, result.rating)
        if result.rating == _RATING_AGAIN:
            return ScheduleOutput(ease_factor=new_ef, interval_days=_FIRST_INTERVAL, repetitions=0)
        interval = self._next_interval(result.interval_days, result.repetitions, new_ef)
        return ScheduleOutput(ease_factor=new_ef, interval_days=interval, repetitions=result.repetitions + 1)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _updated_ease_factor(self, current_ef: float, rating: int) -> float:
        """Clamp the new ease factor to the configured minimum."""
        delta = _EF_DELTA.get(rating, 0.0)
        return max(settings.SM2_MIN_EASE_FACTOR, current_ef + delta)

    def _next_interval(self, current_interval: int, repetitions: int, ef: float) -> int:
        """Calculate the next interval based on repetition count."""
        if repetitions == 0:
            return _FIRST_INTERVAL
        if repetitions == 1:
            return _SECOND_INTERVAL
        return round(current_interval * ef)
