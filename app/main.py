"""StudyOS FastAPI application entry point.

Responsibilities:
- Create the FastAPI app with lifespan (startup / shutdown hooks)
- Register all domain routers under /api/v1
- Register all exception handlers
- Add CORS middleware
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth.router import router as auth_router
from app.api.content.router import router as content_router
from app.api.courses.router import router as courses_router
from app.api.flashcards.router import router as flashcards_router
from app.api.mastery.router import router as mastery_router
from app.api.reviews.router import router as reviews_router
from app.api.sessions.router import router as sessions_router
from app.api.users.router import router as users_router
from app.core.config import settings
from app.core.database import dispose_engine
from app.core.exception_handlers import register_exception_handlers
from app.core.redis import close_redis

logger = logging.getLogger(__name__)

_API_PREFIX = "/api/v1"


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup checks; clean up connections on shutdown."""
    logger.info("StudyOS starting up — env=%s", settings.APP_ENV)
    yield
    logger.info("StudyOS shutting down")
    await dispose_engine()
    await close_redis()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="StudyOS API",
        version="0.1.0",
        description="AI-powered flashcard and spaced repetition platform",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    _add_middleware(app)
    _register_routers(app)
    register_exception_handlers(app)
    return app


def _add_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_routers(app: FastAPI) -> None:
    routers = [
        auth_router,
        users_router,
        courses_router,
        content_router,
        flashcards_router,
        sessions_router,
        reviews_router,
        mastery_router,
    ]
    for router in routers:
        app.include_router(router, prefix=_API_PREFIX)


# ---------------------------------------------------------------------------
# ASGI app — used by uvicorn
# ---------------------------------------------------------------------------

app = create_app()
