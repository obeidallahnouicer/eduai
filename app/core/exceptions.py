"""All domain exceptions for StudyOS.

Rules:
- Every exception inherits from StudyOSException.
- Services raise these; main.py converts them to HTTP responses.
- Never raise HTTPException inside a service.
"""


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class StudyOSException(Exception):
    """Base exception for all StudyOS domain errors."""


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class InvalidCredentialsError(StudyOSException):
    """Raised when email/password combination is incorrect."""


class InvalidTokenError(StudyOSException):
    """Raised when a JWT is missing, malformed, or expired."""


class UserAlreadyExistsError(StudyOSException):
    """Raised when registering with an already-used email."""


class UserNotFoundError(StudyOSException):
    """Raised when a user cannot be found by id or email."""


class InactiveUserError(StudyOSException):
    """Raised when an inactive user attempts to authenticate."""


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

class CourseNotFoundError(StudyOSException):
    """Raised when a course does not exist."""


class CourseAccessDeniedError(StudyOSException):
    """Raised when a user accesses a course they do not own."""


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

class ContentSourceNotFoundError(StudyOSException):
    """Raised when a content source cannot be found."""


class ContentProcessingError(StudyOSException):
    """Raised when file parsing or chunking fails."""


class FileTooLargeError(StudyOSException):
    """Raised when an uploaded file exceeds the size limit."""


class UnsupportedFileTypeError(StudyOSException):
    """Raised when the uploaded file type is not supported."""


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------

class FlashcardNotFoundError(StudyOSException):
    """Raised when a flashcard cannot be found."""


class FlashcardGenerationError(StudyOSException):
    """Raised when AI flashcard generation fails."""


# ---------------------------------------------------------------------------
# Study sessions
# ---------------------------------------------------------------------------

class SessionNotFoundError(StudyOSException):
    """Raised when a study session cannot be found."""


class SessionAlreadyCompletedError(StudyOSException):
    """Raised when trying to submit a review to a finished session."""


# ---------------------------------------------------------------------------
# Mastery
# ---------------------------------------------------------------------------

class MasteryNotFoundError(StudyOSException):
    """Raised when mastery data for a course cannot be found."""
