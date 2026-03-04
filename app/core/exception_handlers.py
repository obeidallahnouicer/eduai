"""Exception handler registry — maps domain exceptions to HTTP responses.

Imported by main.py and registered on the FastAPI app instance.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ContentProcessingError,
    ContentSourceNotFoundError,
    CourseAccessDeniedError,
    CourseNotFoundError,
    FileTooLargeError,
    FlashcardGenerationError,
    FlashcardNotFoundError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    MasteryNotFoundError,
    SessionAlreadyCompletedError,
    SessionNotFoundError,
    StudyOSException,
    UnsupportedFileTypeError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


def _json(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all domain-exception → HTTP-response handlers to *app*."""

    @app.exception_handler(InvalidTokenError)
    async def _invalid_token(_: Request, exc: InvalidTokenError) -> JSONResponse:
        return _json(401, str(exc))

    @app.exception_handler(InvalidCredentialsError)
    async def _invalid_creds(_: Request, exc: InvalidCredentialsError) -> JSONResponse:
        return _json(401, str(exc))

    @app.exception_handler(InactiveUserError)
    async def _inactive_user(_: Request, exc: InactiveUserError) -> JSONResponse:
        return _json(403, str(exc))

    @app.exception_handler(UserAlreadyExistsError)
    async def _user_exists(_: Request, exc: UserAlreadyExistsError) -> JSONResponse:
        return _json(409, str(exc))

    @app.exception_handler(UserNotFoundError)
    async def _user_not_found(_: Request, exc: UserNotFoundError) -> JSONResponse:
        return _json(404, str(exc))

    @app.exception_handler(CourseNotFoundError)
    async def _course_not_found(_: Request, exc: CourseNotFoundError) -> JSONResponse:
        return _json(404, str(exc))

    @app.exception_handler(CourseAccessDeniedError)
    async def _course_access(_: Request, exc: CourseAccessDeniedError) -> JSONResponse:
        return _json(403, str(exc))

    @app.exception_handler(ContentSourceNotFoundError)
    async def _content_not_found(_: Request, exc: ContentSourceNotFoundError) -> JSONResponse:
        return _json(404, str(exc))

    @app.exception_handler(ContentProcessingError)
    async def _content_processing(_: Request, exc: ContentProcessingError) -> JSONResponse:
        return _json(422, str(exc))

    @app.exception_handler(FileTooLargeError)
    async def _file_too_large(_: Request, exc: FileTooLargeError) -> JSONResponse:
        return _json(413, str(exc))

    @app.exception_handler(UnsupportedFileTypeError)
    async def _unsupported_type(_: Request, exc: UnsupportedFileTypeError) -> JSONResponse:
        return _json(415, str(exc))

    @app.exception_handler(FlashcardNotFoundError)
    async def _flashcard_not_found(_: Request, exc: FlashcardNotFoundError) -> JSONResponse:
        return _json(404, str(exc))

    @app.exception_handler(FlashcardGenerationError)
    async def _flashcard_gen(_: Request, exc: FlashcardGenerationError) -> JSONResponse:
        return _json(502, str(exc))

    @app.exception_handler(SessionNotFoundError)
    async def _session_not_found(_: Request, exc: SessionNotFoundError) -> JSONResponse:
        return _json(404, str(exc))

    @app.exception_handler(SessionAlreadyCompletedError)
    async def _session_done(_: Request, exc: SessionAlreadyCompletedError) -> JSONResponse:
        return _json(409, str(exc))

    @app.exception_handler(MasteryNotFoundError)
    async def _mastery_not_found(_: Request, exc: MasteryNotFoundError) -> JSONResponse:
        return _json(404, str(exc))

    @app.exception_handler(StudyOSException)
    async def _studyos_fallback(_: Request, exc: StudyOSException) -> JSONResponse:
        return _json(500, str(exc))
