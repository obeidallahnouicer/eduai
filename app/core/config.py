"""Application settings — reads from .env via pydantic-settings."""

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_URL: str

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ------------------------------------------------------------------
    # AI (NVIDIA NIM — OpenAI-compatible)
    # ------------------------------------------------------------------
    NVIDIA_API_KEY: str
    OPENAI_BASE_URL: AnyHttpUrl = Field(default="https://integrate.api.nvidia.com/v1")  # type: ignore[assignment]
    OPENAI_MODEL: str = "openai/gpt-oss-120b"
    AI_CACHE_TTL_SECONDS: int = 86_400
    AI_MAX_CHUNKS_PER_REQUEST: int = 20
    AI_TEMPERATURE: float = 1.0
    AI_TOP_P: float = 1.0
    AI_MAX_TOKENS: int = 4096

    # ------------------------------------------------------------------
    # File storage
    # ------------------------------------------------------------------
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ------------------------------------------------------------------
    # SRS
    # ------------------------------------------------------------------
    MAX_CARDS_PER_SESSION: int = 20
    SM2_INITIAL_EASE_FACTOR: float = 2.5
    SM2_MIN_EASE_FACTOR: float = 1.3

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()  # type: ignore[call-arg]
