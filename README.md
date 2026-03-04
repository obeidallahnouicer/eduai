# StudyOS — AI-Powered Spaced Repetition Platform

> **StudyOS** is a production-ready, async FastAPI backend that turns any document (PDF or text) into a personalised flashcard study system. Upload study material → the platform uses an LLM to generate flashcards → a SuperMemo-2 (SM-2) algorithm schedules reviews → a WebSocket-driven live session delivers cards in real time → mastery scores track progress per topic.

---

## Table of Contents

1. [Feature Overview](#feature-overview)
2. [Tech Stack](#tech-stack)
3. [Architecture Overview](#architecture-overview)
4. [Directory Structure](#directory-structure)
5. [Domain Model (ERD)](#domain-model-erd)
6. [API Reference](#api-reference)
7. [Request / Response Flow](#request--response-flow)
8. [AI Pipeline](#ai-pipeline)
9. [Spaced Repetition (SM-2)](#spaced-repetition-sm-2)
10. [WebSocket Study Session](#websocket-study-session)
11. [Security Model](#security-model)
12. [Configuration Reference](#configuration-reference)
13. [Database Migrations](#database-migrations)
14. [Docker & Deployment](#docker--deployment)
15. [Development Setup](#development-setup)
16. [Error Handling Strategy](#error-handling-strategy)
17. [Testing](#testing)

---

## Feature Overview

| Feature | Details |
|---|---|
| **User Auth** | Register / Login / Refresh with JWT (access + refresh tokens), bcrypt passwords |
| **Courses** | Full CRUD; every resource is scoped to its owning user |
| **Content Ingestion** | Upload PDF or plain-text files (≤ 50 MB); SHA-256 dedup; async local storage |
| **AI Flashcard Generation** | NVIDIA NIM (OpenAI-compatible) LLM with Redis-cached results; streaming response |
| **Manual Flashcards** | Create, patch, archive, and delete cards; difficulty 1–5 |
| **Study Sessions** | REST to open a session, WebSocket to drive the live review loop |
| **SM-2 Scheduling** | Stateless, pure-Python implementation of the SuperMemo-2 algorithm |
| **Card Reviews** | Submit a rating (again/hard/good/easy); next review date computed and persisted |
| **Mastery Scores** | Per-topic aggregated score recomputed on demand from review history |
| **CORS** | Configurable allowed-origins list |
| **OpenAPI Docs** | Auto-generated Swagger UI (`/api/docs`) and ReDoc (`/api/redoc`) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Web framework** | [FastAPI](https://fastapi.tiangolo.com/) 0.115+ with async lifespan |
| **ASGI server** | [Uvicorn](https://www.uvicorn.org/) with standard extras |
| **Database** | PostgreSQL 15 via [asyncpg](https://github.com/MagicStack/asyncpg) |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 (async) |
| **Migrations** | [Alembic](https://alembic.sqlalchemy.org/) |
| **Cache / Broker** | [Redis](https://redis.io/) 7 |
| **AI Provider** | NVIDIA NIM (`openai/gpt-oss-120b`) via OpenAI-compatible SDK |
| **PDF Parsing** | [PyMuPDF](https://pymupdf.readthedocs.io/) (fitz) |
| **Auth** | [python-jose](https://python-jose.readthedocs.io/) (JWT) + [passlib](https://passlib.readthedocs.io/) (bcrypt) |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) + pydantic-settings |
| **Containerisation** | Docker (multi-stage) + Docker Compose |
| **Language** | Python 3.11+ |

---

## Architecture Overview

```mermaid
graph TB
    subgraph Client["Client Layer"]
        WEB["Web / Mobile Client"]
        WS_CLIENT["WebSocket Client"]
    end

    subgraph Gateway["API Gateway"]
        CORS["CORS Middleware"]
        AUTH_MW["Bearer Token Guard<br/>(deps.py)"]
    end

    subgraph API["API Layer  (/api/v1)"]
        AUTH["/auth<br/>register · login · refresh"]
        USERS["/users<br/>profile"]
        COURSES["/courses<br/>CRUD"]
        CONTENT["/content<br/>upload · chunks"]
        FLASHCARDS["/flashcards<br/>CRUD · generate"]
        SESSIONS["/sessions<br/>create · WS loop"]
        REVIEWS["/reviews<br/>submit rating"]
        MASTERY["/mastery<br/>scores · recompute"]
    end

    subgraph Services["Service Layer"]
        AUTH_SVC["AuthService"]
        COURSE_SVC["CourseService"]
        CONTENT_SVC["ContentService"]
        FLASH_SVC["FlashcardService"]
        SESSION_SVC["SessionService"]
        REVIEW_SVC["ReviewService"]
        MASTERY_SVC["MasteryService"]
    end

    subgraph Infrastructure["Infrastructure / Shared Services"]
        LLM["LLMClient<br/>(NVIDIA NIM)"]
        SM2["SM2Algorithm"]
        STORAGE["LocalStorage"]
        CACHE["RedisCache"]
        DB["AsyncSession<br/>(PostgreSQL)"]
    end

    WEB -->|HTTP REST| CORS
    WS_CLIENT -->|WebSocket| SESSIONS
    CORS --> AUTH_MW
    AUTH_MW --> API

    AUTH --> AUTH_SVC
    USERS --> AUTH_SVC
    COURSES --> COURSE_SVC
    CONTENT --> CONTENT_SVC
    FLASHCARDS --> FLASH_SVC
    SESSIONS --> SESSION_SVC
    REVIEWS --> REVIEW_SVC
    MASTERY --> MASTERY_SVC

    FLASH_SVC --> LLM
    FLASH_SVC --> CONTENT_SVC
    REVIEW_SVC --> SM2
    CONTENT_SVC --> STORAGE
    LLM --> CACHE

    AUTH_SVC --> DB
    COURSE_SVC --> DB
    CONTENT_SVC --> DB
    FLASH_SVC --> DB
    SESSION_SVC --> DB
    REVIEW_SVC --> DB
    MASTERY_SVC --> DB
```

---

## Directory Structure

```
studyos-backend/
├── app/
│   ├── main.py                  # App factory, router registration, lifespan
│   ├── api/
│   │   ├── deps.py              # Shared FastAPI dependencies (auth guard)
│   │   ├── auth/                # Register · Login · Refresh
│   │   ├── users/               # User profile endpoints
│   │   ├── courses/             # Course CRUD
│   │   ├── content/             # File upload, PDF/text parsing, chunking
│   │   ├── flashcards/          # Manual creation + AI generation
│   │   ├── sessions/            # Study session REST + WebSocket handler
│   │   ├── reviews/             # Submit card review + SM-2 scheduling
│   │   └── mastery/             # Per-topic mastery score retrieval + recompute
│   ├── core/
│   │   ├── config.py            # Pydantic-settings (reads .env)
│   │   ├── database.py          # Async SQLAlchemy engine & session factory
│   │   ├── redis.py             # Redis connection management
│   │   ├── security.py          # JWTHandler + bcrypt helpers
│   │   ├── exceptions.py        # Domain exception hierarchy
│   │   └── exception_handlers.py# Maps domain exceptions → HTTP responses
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── base.py              # DeclarativeBase with UUID PK + timestamps
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── content_source.py
│   │   ├── flashcard.py
│   │   ├── study_session.py
│   │   ├── card_review.py
│   │   └── mastery_score.py
│   └── services/
│       ├── ai/
│       │   ├── base.py          # AIClient ABC + FlashcardData dataclass
│       │   ├── llm_client.py    # NVIDIA NIM concrete implementation
│       │   └── prompts.py       # Prompt template constants
│       ├── cache/
│       │   ├── base.py          # CacheClient ABC
│       │   └── redis_cache.py   # Redis concrete implementation
│       ├── srs/
│       │   ├── base.py          # SRSAlgorithm ABC + ReviewResult / ScheduleOutput
│       │   └── sm2.py           # SuperMemo-2 stateless implementation
│       └── storage/
│           ├── base.py          # FileStorage ABC
│           └── local_storage.py # Disk-based concrete implementation
├── migrations/
│   ├── env.py                   # Alembic async env
│   └── versions/
│       └── 0001_initial_schema.py
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile                   # Multi-stage (builder → runtime)
├── docker-compose.yml           # api · postgres · redis · migrate
├── pyproject.toml               # Hatchling build + dependencies
└── alembic.ini
```

Each API sub-package follows the same structure:

```
<domain>/
├── __init__.py
├── router.py    # HTTP/WS routes only — no business logic
├── schemas.py   # Pydantic request/response models
└── service.py   # Business logic — only raises domain exceptions
```

---

## Domain Model (ERD)

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string full_name
        text hashed_password
        string role
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    COURSES {
        uuid id PK
        uuid owner_id FK
        string title
        text description
        boolean is_archived
        timestamptz created_at
        timestamptz updated_at
    }

    CONTENT_SOURCES {
        uuid id PK
        uuid course_id FK
        uuid uploaded_by FK
        string type
        text storage_path
        string original_name
        boolean is_processed
        string content_hash
        timestamptz created_at
        timestamptz updated_at
    }

    FLASHCARDS {
        uuid id PK
        uuid course_id FK
        uuid content_source_id FK
        uuid created_by FK
        text front
        text back
        string topic
        smallint difficulty
        string origin
        boolean is_archived
        timestamptz created_at
        timestamptz updated_at
    }

    STUDY_SESSIONS {
        uuid id PK
        uuid user_id FK
        uuid course_id FK
        timestamptz started_at
        timestamptz ended_at
        int cards_reviewed
        int cards_mastered
        timestamptz created_at
        timestamptz updated_at
    }

    CARD_REVIEWS {
        uuid id PK
        uuid flashcard_id FK
        uuid user_id FK
        uuid session_id FK
        string result
        numeric ease_factor
        int interval_days
        timestamptz next_review_at
        timestamptz reviewed_at
        timestamptz created_at
        timestamptz updated_at
    }

    MASTERY_SCORES {
        uuid id PK
        uuid user_id FK
        uuid course_id FK
        string topic
        numeric score
        timestamptz last_updated
        timestamptz created_at
        timestamptz updated_at
    }

    USERS ||--o{ COURSES : "owns"
    USERS ||--o{ CONTENT_SOURCES : "uploads"
    USERS ||--o{ FLASHCARDS : "creates"
    USERS ||--o{ STUDY_SESSIONS : "starts"
    USERS ||--o{ CARD_REVIEWS : "submits"
    USERS ||--o{ MASTERY_SCORES : "has"
    COURSES ||--o{ CONTENT_SOURCES : "contains"
    COURSES ||--o{ FLASHCARDS : "has"
    COURSES ||--o{ STUDY_SESSIONS : "scoped to"
    COURSES ||--o{ MASTERY_SCORES : "measured in"
    CONTENT_SOURCES ||--o{ FLASHCARDS : "generates"
    FLASHCARDS ||--o{ CARD_REVIEWS : "reviewed in"
    STUDY_SESSIONS ||--o{ CARD_REVIEWS : "contains"
```

---

## API Reference

All routes are served under the `/api/v1` prefix. Interactive docs are available at `/api/docs`.

### Authentication — `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | Public | Create a new user account |
| `POST` | `/auth/login` | Public | Validate credentials; receive access + refresh tokens |
| `POST` | `/auth/refresh` | Public | Rotate token pair using a valid refresh token |

### Users — `/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/users/me` | Bearer | Return the current authenticated user's profile |

### Courses — `/courses`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/courses` | Bearer | Create a course |
| `GET` | `/courses` | Bearer | List all courses owned by the current user |
| `GET` | `/courses/{id}` | Bearer | Retrieve a single course |
| `PATCH` | `/courses/{id}` | Bearer | Update title / description / archived flag |
| `DELETE` | `/courses/{id}` | Bearer | Hard-delete a course (cascades to all children) |

### Content — `/content`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/content/upload` | Bearer | Upload a PDF or text file; creates a `ContentSource` |
| `GET` | `/content/{id}/chunks` | Bearer | Parse the file and return overlapping text chunks |

### Flashcards — `/flashcards`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/flashcards` | Bearer | Create a single manual flashcard |
| `GET` | `/flashcards?course_id=` | Bearer | List all active flashcards for a course |
| `PATCH` | `/flashcards/{id}` | Bearer | Update front / back / topic / difficulty / archived |
| `DELETE` | `/flashcards/{id}` | Bearer | Hard-delete a flashcard |
| `POST` | `/flashcards/generate` | Bearer | Trigger AI generation from a `content_source_id` |

### Sessions — `/sessions`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/sessions` | Bearer | Open a new study session for a course |
| `WS` | `/sessions/{id}` | — | WebSocket: drives the live card review loop |

### Reviews — `/reviews`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/reviews` | Bearer | Submit a card rating; SM-2 computes next review date |

### Mastery — `/mastery`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/mastery?course_id=` | Bearer | Return current mastery scores per topic |
| `POST` | `/mastery/recompute` | Bearer | Recompute all mastery scores from review history |

---

## Request / Response Flow

### REST Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as CORS + Bearer Guard
    participant R as Router
    participant S as Service
    participant DB as PostgreSQL
    participant EH as Exception Handler

    C->>MW: HTTP Request + Bearer Token
    MW->>MW: Decode JWT → User
    MW->>R: Validated User + Request Body
    R->>S: Call service method
    S->>DB: Async query (AsyncSession)
    DB-->>S: ORM result
    S-->>R: Pydantic Response model
    R-->>C: 200/201 JSON

    note over S,EH: On domain exception
    S--xEH: Raise StudyOSException subclass
    EH-->>C: Mapped HTTP error (4xx/5xx)
```

### AI Flashcard Generation Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant FS as FlashcardService
    participant CS as ContentService
    participant ST as LocalStorage
    participant CH as TextChunker
    participant LLM as LLMClient
    participant RC as RedisCache
    participant NV as NVIDIA NIM API
    participant DB as PostgreSQL

    C->>FS: POST /flashcards/generate {content_source_id}
    FS->>CS: get_chunks(content_source_id)
    CS->>DB: Fetch ContentSource row
    CS->>ST: Load raw file bytes
    CS->>CH: parse_file() → extract text
    CH-->>CS: Plain text string
    CS->>CH: chunk(text) → 1500-char windows
    CH-->>CS: []string chunks
    CS-->>FS: chunks[]
    FS->>LLM: generate_flashcards(chunks, course_title)
    LLM->>RC: GET cache_key (SHA-256 of content)
    alt Cache hit
        RC-->>LLM: Cached FlashcardData[]
    else Cache miss
        LLM->>NV: Stream chat completion
        NV-->>LLM: JSON array (streamed)
        LLM->>LLM: Parse JSON → FlashcardData[]
        LLM->>RC: SET cache_key TTL=24h
    end
    LLM-->>FS: FlashcardData[]
    FS->>DB: INSERT flashcards (origin=ai)
    FS-->>C: FlashcardResponse[]
```

---

## AI Pipeline

The AI pipeline is built around two abstract interfaces and a single concrete implementation:

```mermaid
classDiagram
    class AIClient {
        <<abstract>>
        +generate_flashcards(chunks, course_title) FlashcardData[]
    }

    class LLMClient {
        -cache: CacheClient
        -client: AsyncOpenAI
        +generate_flashcards(chunks, course_title) FlashcardData[]
        -_call_llm(chunks, course_title) FlashcardData[]
        -_stream_response(user_prompt) str
        -_parse_response(raw) FlashcardData[]
        -_build_cache_key(chunks, title) str
    }

    class CacheClient {
        <<abstract>>
        +get(key) Any
        +set(key, value, ttl) None
        +delete(key) None
    }

    class RedisCache {
        -redis: Redis
        +get(key) Any
        +set(key, value, ttl) None
        +delete(key) None
    }

    class FlashcardData {
        +front: str
        +back: str
        +topic: str
        +difficulty: int
    }

    AIClient <|-- LLMClient
    CacheClient <|-- RedisCache
    LLMClient --> CacheClient
    LLMClient ..> FlashcardData : produces
```

**Prompt strategy:**
- **System prompt** — instructs the model to act as an expert educator and return a strictly-typed JSON array.
- **User prompt** — passes `course_title` for domain context and up to `AI_MAX_CHUNKS_PER_REQUEST` (default 20) text chunks.
- **Cache key** — deterministic SHA-256 of `course_title + all_chunks`; results are cached for `AI_CACHE_TTL_SECONDS` (default 24 h).

---

## Spaced Repetition (SM-2)

StudyOS implements the classic [SuperMemo SM-2 algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2) as a **pure, stateless** function. All mutable state lives in `card_reviews` rows.

### Rating Scale

| Value | Label | Meaning |
|-------|-------|---------|
| `0` | Again | Complete blackout — restart interval |
| `1` | Hard | Significant difficulty |
| `2` | Good | Correct with hesitation |
| `3` | Easy | Perfect recall |

### Algorithm

```mermaid
flowchart TD
    A[Card reviewed with rating R] --> B{R == 0?}
    B -- Yes --> C[Reset: interval=1d, repetitions=0]
    B -- No --> D[Compute new ease factor\nEF += delta_R\nEF = max EF_min]
    D --> E{repetitions == 0?}
    E -- Yes --> F[interval = 1d]
    E -- No --> G{repetitions == 1?}
    G -- Yes --> H[interval = 6d]
    G -- No --> I[interval = round prev_interval x EF]
    F --> J[repetitions += 1]
    H --> J
    I --> J
    C --> K[Persist CardReview\nnext_review_at = now + interval]
    J --> K
    K --> L[Update MasteryScore on demand]
```

**Ease factor deltas:**

| Rating | ΔEF |
|--------|-----|
| Again (0) | −0.20 |
| Hard (1) | −0.15 |
| Good (2) | 0.00 |
| Easy (3) | +0.10 |

The minimum ease factor is clamped at `SM2_MIN_EASE_FACTOR` (default `1.3`); initial value is `SM2_INITIAL_EASE_FACTOR` (default `2.5`).

---

## WebSocket Study Session

The `/api/v1/sessions/{session_id}` WebSocket endpoint drives a full interactive review loop server-side.

```mermaid
sequenceDiagram
    participant C as Client (WebSocket)
    participant H as SessionHandler
    participant SS as SessionService
    participant SM as SM2Algorithm
    participant DB as PostgreSQL

    C->>H: WS Connect
    H->>SS: get_due_cards(session_id)
    SS->>DB: SELECT flashcards WHERE course_id = ...<br/>LIMIT MAX_CARDS_PER_SESSION
    DB-->>SS: Flashcard[]
    SS-->>H: Flashcard[]

    loop For each card
        H->>C: send WSCardEvent {id, front, back, topic}
        C->>H: send WSReviewEvent {rating, ...}
        H->>SM: compute_next_review(ReviewResult)
        SM-->>H: ScheduleOutput
        H->>SS: increment_reviewed(session_id)
        SS->>DB: UPDATE cards_reviewed += 1
    end

    H->>SS: close(session_id, mastered_count)
    SS->>DB: UPDATE ended_at, cards_mastered
    H->>C: WS Close
```

**Message schemas:**

`WSCardEvent` (server → client):
```json
{
  "flashcard_id": "uuid",
  "front": "What is the powerhouse of the cell?",
  "back": "The mitochondria",
  "topic": "Cell Biology"
}
```

`WSReviewEvent` (client → server):
```json
{
  "rating": 2
}
```

---

## Security Model

```mermaid
flowchart LR
    subgraph Token["Token Lifecycle"]
        REG["Register"] --> HASH["bcrypt hash\npassword"]
        HASH --> STORE["Store User row"]
        LOGIN["Login"] --> VERIFY["Verify bcrypt"]
        VERIFY --> ISSUE["Issue\nAccess Token 30m\nRefresh Token 7d"]
        REFRESH["Refresh"] --> DECODE_R["Decode refresh\ntoken (HS256)"]
        DECODE_R --> ISSUE
    end

    subgraph Guard["Request Guard (deps.py)"]
        REQ["Incoming Request"] --> BEARER["Extract Bearer token"]
        BEARER --> DECODE_A["jwt_handler.decode_access_token()"]
        DECODE_A --> LOAD["Load User from DB"]
        LOAD --> ACTIVE{"is_active?"}
        ACTIVE -- No --> ERR403["403 Forbidden"]
        ACTIVE -- Yes --> ROUTE["Proceed to route handler"]
    end
```

- **Passwords** — bcrypt via `passlib` with automatic cost-factor handling.
- **Access tokens** — HS256 JWT, signed with `APP_SECRET_KEY`, expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 min).
- **Refresh tokens** — same signing key; `type` claim distinguishes them from access tokens; expire after `REFRESH_TOKEN_EXPIRE_DAYS` (default 7 days).
- **Non-root container** — Dockerfile creates a dedicated `appuser` with no shell.

---

## Configuration Reference

All settings are read from a `.env` file (or real environment variables). Create a `.env` file by copying the table below:

| Variable | Default | Required | Description |
|---|---|---|---|
| `APP_ENV` | `development` | | Runtime environment label |
| `APP_DEBUG` | `false` | | Enables SQLAlchemy query echo |
| `APP_SECRET_KEY` | — | ✅ | HS256 signing key for JWTs |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | | Comma-separated CORS origins |
| `DATABASE_URL` | — | ✅ | `postgresql+asyncpg://user:pass@host/db` |
| `DATABASE_POOL_SIZE` | `10` | | SQLAlchemy connection pool size |
| `DATABASE_MAX_OVERFLOW` | `20` | | Extra connections above pool size |
| `REDIS_URL` | — | ✅ | `redis://host:6379/0` |
| `JWT_ALGORITHM` | `HS256` | | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | | Refresh token lifetime |
| `NVIDIA_API_KEY` | — | ✅ | NVIDIA NIM API key |
| `OPENAI_BASE_URL` | `https://integrate.api.nvidia.com/v1` | | NIM endpoint (OpenAI-compatible) |
| `OPENAI_MODEL` | `openai/gpt-oss-120b` | | Model ID to use |
| `AI_CACHE_TTL_SECONDS` | `86400` | | Redis TTL for cached LLM results |
| `AI_MAX_CHUNKS_PER_REQUEST` | `20` | | Max text chunks sent to LLM per call |
| `AI_TEMPERATURE` | `1.0` | | LLM sampling temperature |
| `AI_TOP_P` | `1.0` | | LLM nucleus sampling |
| `AI_MAX_TOKENS` | `4096` | | Max tokens in LLM response |
| `UPLOAD_DIR` | `uploads` | | Directory for stored files |
| `MAX_UPLOAD_SIZE_MB` | `50` | | Maximum upload file size |
| `MAX_CARDS_PER_SESSION` | `20` | | Cards served per study session |
| `SM2_INITIAL_EASE_FACTOR` | `2.5` | | SM-2 starting ease factor |
| `SM2_MIN_EASE_FACTOR` | `1.3` | | SM-2 minimum ease factor clamp |

---

## Database Migrations

Migrations are managed with **Alembic** and run against the async `asyncpg` driver.

```bash
# Apply all pending migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Auto-generate a new migration from model changes
alembic revision --autogenerate -m "describe_change"

# Show current revision
alembic current
```

The initial migration (`0001_initial_schema.py`) creates all seven tables:

```mermaid
graph LR
    M0001["0001_initial_schema\n• users\n• courses\n• content_sources\n• flashcards\n• study_sessions\n• card_reviews\n• mastery_scores"]
```

---

## Docker & Deployment

### Services

```mermaid
graph TD
    subgraph Compose["docker-compose stack"]
        API["api\nFastAPI + Uvicorn\n:8000"]
        MIGRATE["migrate\nAlembic upgrade head\n(runs once)"]
        PG["postgres:15-alpine\n:5432"]
        RD["redis:7-alpine\n:6379"]
    end

    API -->|asyncpg| PG
    API -->|redis-py| RD
    MIGRATE -->|asyncpg| PG
    API -.->|depends_on healthy| PG
    API -.->|depends_on healthy| RD
    MIGRATE -.->|depends_on healthy| PG
```

### Quick Start

```bash
# 1. Clone and create environment file
cp .env.example .env   # fill in APP_SECRET_KEY and NVIDIA_API_KEY

# 2. Build and start the full stack
docker compose up --build

# 3. Run migrations (handled automatically by the 'migrate' service)
# The API will be available at http://localhost:8000
# Swagger UI: http://localhost:8000/api/docs
```

### Dockerfile — Multi-Stage Build

| Stage | Base | Purpose |
|---|---|---|
| `builder` | `python:3.11-slim` | Install all dependencies (including dev) into `/opt/venv` |
| `runtime` | `python:3.11-slim` | Copy venv + application source only; run as `appuser` |

The two-stage build keeps the final image lean by excluding build tools (`build-essential`, `libpq-dev`) from the runtime layer.

---

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15
- Redis 7
- (Optional) Docker + Docker Compose

### Local Installation

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install all dependencies including dev extras
pip install -e ".[dev]"

# Copy and populate the environment file
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the development server with hot-reload
uvicorn app.main:app --reload --port 8000
```

### Code Quality

The project uses **Ruff** for linting and formatting, and **mypy** for static type checking:

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy app/
```

---

## Error Handling Strategy

All business errors inherit from `StudyOSException`. Services **only** raise domain exceptions — never `HTTPException`. The global exception handler registry in `exception_handlers.py` maps each exception type to the correct HTTP status code.

```mermaid
classDiagram
    class StudyOSException {
        <<base>>
    }

    class InvalidCredentialsError { }
    class InvalidTokenError { }
    class UserAlreadyExistsError { }
    class UserNotFoundError { }
    class InactiveUserError { }

    class CourseNotFoundError { }
    class CourseAccessDeniedError { }

    class ContentSourceNotFoundError { }
    class ContentProcessingError { }
    class FileTooLargeError { }
    class UnsupportedFileTypeError { }

    class FlashcardNotFoundError { }
    class FlashcardGenerationError { }

    class SessionNotFoundError { }
    class SessionAlreadyCompletedError { }

    class MasteryNotFoundError { }

    StudyOSException <|-- InvalidCredentialsError
    StudyOSException <|-- InvalidTokenError
    StudyOSException <|-- UserAlreadyExistsError
    StudyOSException <|-- UserNotFoundError
    StudyOSException <|-- InactiveUserError
    StudyOSException <|-- CourseNotFoundError
    StudyOSException <|-- CourseAccessDeniedError
    StudyOSException <|-- ContentSourceNotFoundError
    StudyOSException <|-- ContentProcessingError
    StudyOSException <|-- FileTooLargeError
    StudyOSException <|-- UnsupportedFileTypeError
    StudyOSException <|-- FlashcardNotFoundError
    StudyOSException <|-- FlashcardGenerationError
    StudyOSException <|-- SessionNotFoundError
    StudyOSException <|-- SessionAlreadyCompletedError
    StudyOSException <|-- MasteryNotFoundError
```

**HTTP mapping:**

| Exception | HTTP Status |
|---|---|
| `InvalidTokenError` / `InvalidCredentialsError` | 401 Unauthorized |
| `InactiveUserError` / `CourseAccessDeniedError` | 403 Forbidden |
| `*NotFoundError` | 404 Not Found |
| `ContentProcessingError` | 422 Unprocessable Entity |
| `FileTooLargeError` | 413 Content Too Large |
| `UnsupportedFileTypeError` | 415 Unsupported Media Type |
| `UserAlreadyExistsError` | 409 Conflict |

---

## Testing

The project uses **pytest** with `pytest-asyncio` for async test support and `httpx` for test client requests.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

Test layout:

```
tests/
├── unit/           # Pure logic tests (SM-2, chunker, parsers, etc.)
└── integration/    # Tests against a real (test) database and Redis
```

---

## License

MIT — see `LICENSE` for details.
