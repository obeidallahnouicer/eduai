<!--
Copilot Task:
Upgrade this README into a professional engineering documentation page.
Include architecture diagrams (Mermaid), system flow, design patterns, and clear technical explanations.
-->

# StudyOS — AI-Powered Spaced Repetition Platform

**StudyOS** is a production-ready, async FastAPI backend that transforms any document (PDF or plain text) into a personalised flashcard study system. An LLM generates flashcards from uploaded content, a SuperMemo-2 (SM-2) algorithm schedules reviews based on recall performance, and a WebSocket-driven live session delivers cards in real time while mastery scores track progress per topic.

---

# Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Data Flow / Processing Pipeline](#data-flow--processing-pipeline)
4. [Project Structure](#project-structure)
5. [Design Decisions](#design-decisions)
6. [Design Patterns Used](#design-patterns-used)
7. [Tech Stack](#tech-stack)
8. [Installation](#installation)
9. [Usage](#usage)
10. [API Reference](#api-reference)
11. [Domain Model (ERD)](#domain-model-erd)
12. [Spaced Repetition (SM-2)](#spaced-repetition-sm-2)
13. [WebSocket Study Session](#websocket-study-session)
14. [Security Model](#security-model)
15. [Configuration Reference](#configuration-reference)
16. [Database Migrations](#database-migrations)
17. [Error Handling](#error-handling)
18. [Testing](#testing)
19. [Future Improvements](#future-improvements)

---

# System Overview

StudyOS solves the problem of passive learning from documents. Users upload study material and the platform automates the full active-recall workflow:

| Stage | What Happens |
|---|---|
| **Ingest** | User uploads a PDF or text file (≤ 50 MB); file is stored locally and deduplicated via SHA-256 |
| **Generate** | An LLM (NVIDIA NIM, OpenAI-compatible) reads overlapping text chunks and produces structured flashcards (front / back / topic / difficulty) |
| **Schedule** | Each card review is scored (again / hard / good / easy) and the SM-2 algorithm computes the next optimal review date |
| **Study** | A WebSocket session streams due cards to the client in real time; the server records every review and updates the session counters |
| **Measure** | Per-topic mastery scores are derived from review history on demand |

**Key capabilities:**

- Full user authentication with JWT access + refresh tokens and bcrypt-hashed passwords
- Course-scoped resource ownership (every object belongs to a user + course)
- Redis caching of LLM results (24h TTL, keyed by SHA-256 of content)
- Configurable CORS, rate limits, and LLM parameters via environment variables
- Auto-generated OpenAPI docs at `/api/docs` (Swagger UI) and `/api/redoc`

---

# Architecture

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

# Data Flow / Processing Pipeline

## Content Ingestion and AI Generation

```mermaid
flowchart LR
    Upload["📄 File Upload\n(PDF / Text)"] --> Dedup["SHA-256\nDeduplication"]
    Dedup --> Store["Local\nStorage"]
    Store --> Parse["File Parser\n(PyMuPDF / text)"]
    Parse --> Chunk["Text Chunker\n1500-char windows"]
    Chunk --> Cache{"Redis\nCache?"}
    Cache -- Hit --> Cards["FlashcardData[]"]
    Cache -- Miss --> LLM["NVIDIA NIM\nLLM (streaming)"]
    LLM --> Parse2["JSON\nParser"]
    Parse2 --> CacheWrite["Cache SET\nTTL 24h"]
    CacheWrite --> Cards
    Cards --> DB["PostgreSQL\n(INSERT flashcards)"]
```

## Study Session Flow

```mermaid
flowchart LR
    Start["POST /sessions\n(open session)"] --> Load["Load due cards\nfor course"]
    Load --> WS["WebSocket\nconnect"]
    WS --> Send["Server sends\nWSCardEvent"]
    Send --> Review["Client submits\nWSReviewEvent\n(rating 0–3)"]
    Review --> SM2["SM-2\nScheduler"]
    SM2 --> Save["Persist\nCardReview +\nnext_review_at"]
    Save --> More{"More\ncards?"}
    More -- Yes --> Send
    More -- No --> Close["Close session\nupdate counters"]
```

## REST Request Lifecycle

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

## AI Flashcard Generation (Detailed)

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

# Project Structure

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

# Design Decisions

## Async-First Architecture

FastAPI with `asyncpg` and SQLAlchemy 2.0 async was chosen to maximise I/O concurrency without the operational cost of a message queue. All database queries, file reads, and LLM calls are awaited on the same event loop, keeping the thread pool free for CPU-bound work.

| Decision | Rationale | Tradeoff |
|---|---|---|
| **Async SQLAlchemy + asyncpg** | Non-blocking DB I/O; handles burst traffic on a single process | Slightly more complex session management than synchronous ORM |
| **NVIDIA NIM via OpenAI SDK** | Drop-in compatibility with the OpenAI client; swap models by changing `OPENAI_MODEL` env var | Vendor dependency; requires valid API key |
| **Redis caching for LLM results** | Identical document + title combinations re-use cached flashcards; eliminates redundant API cost | Cache invalidation is manual; staleness possible if prompts change |
| **SM-2 as a pure stateless function** | No background scheduler needed; next review date computed inline at review time | Requires querying review history to reconstruct state |
| **Domain exception hierarchy** | Routers never catch exceptions; a single registry maps each type to HTTP status | Slightly more boilerplate than throwing `HTTPException` directly |
| **Multi-stage Docker build** | Runtime image excludes build tools; smaller attack surface and image size | Slightly more complex Dockerfile |

## Scalability Considerations

- **Horizontal scaling** — the API is stateless (JWT auth, no server-side sessions); multiple API instances can run behind a load balancer sharing the same PostgreSQL and Redis.
- **Connection pooling** — `DATABASE_POOL_SIZE` (default 10) and `DATABASE_MAX_OVERFLOW` (default 20) are tunable per instance.
- **LLM cost control** — Redis cache with a 24h TTL prevents redundant calls for the same content. `AI_MAX_CHUNKS_PER_REQUEST` limits tokens per request.
- **File storage** — the current `LocalStorage` implementation writes to disk; replacing it with an S3-compatible adapter (matching the `FileStorage` ABC) requires no changes to the service layer.

---

# Design Patterns Used

| Pattern | Where | Description |
|---|---|---|
| **Service Layer** | `app/services/`, `app/api/*/service.py` | All business logic lives in service classes. Routers are thin — they validate input, call a service method, and return the result. |
| **Repository / Abstract Interface** | `app/services/ai/base.py`, `app/services/cache/base.py`, `app/services/srs/base.py`, `app/services/storage/base.py` | Each infrastructure concern (LLM, cache, SRS algorithm, file storage) is hidden behind an Abstract Base Class. Concrete implementations are swappable without touching service code. |
| **Dependency Injection** | `app/api/deps.py`, FastAPI `Depends()` | Authentication, database sessions, and service instances are injected into route handlers via FastAPI's `Depends()` mechanism. |
| **Pipeline Pattern** | Content ingestion → chunking → LLM generation → persist | File upload triggers a sequential chain: parse → chunk → cache-or-LLM → insert. Each step transforms a data structure and passes it to the next. |
| **Adapter Pattern** | `LLMClient` wrapping `AsyncOpenAI` | The NVIDIA NIM endpoint is accessed through the standard OpenAI Python SDK, adapting a third-party interface to the internal `AIClient` ABC. |
| **Domain Exception Hierarchy** | `app/core/exceptions.py` + `exception_handlers.py` | A tree of typed domain exceptions is caught at the framework boundary and translated to HTTP responses. Services raise domain exceptions; routers never see `HTTPException`. |

---

# Tech Stack

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
| **Code Quality** | Ruff (lint + format) + mypy (type checking) |
| **Testing** | pytest + pytest-asyncio + httpx |
| **Language** | Python 3.11+ |

---

# Domain Model (ERD)

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

# API Reference

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

# Spaced Repetition (SM-2)

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

# WebSocket Study Session

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

# Security Model

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

# Configuration Reference

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

# Database Migrations

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

# Installation

## Option A — Docker Compose (Recommended)

Docker Compose starts the full stack (API, PostgreSQL, Redis) and runs migrations automatically via a dedicated `migrate` service.

### Stack Layout

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

### Dockerfile — Multi-Stage Build

| Stage | Base | Purpose |
|---|---|---|
| `builder` | `python:3.11-slim` | Install all dependencies (including dev) into `/opt/venv` |
| `runtime` | `python:3.11-slim` | Copy venv + application source only; run as `appuser` |

The two-stage build excludes build tools (`build-essential`, `libpq-dev`) from the runtime layer, keeping the image lean and reducing the attack surface.

```bash
# 1. Copy and populate the environment file
cp .env.example .env   # fill in APP_SECRET_KEY and NVIDIA_API_KEY at minimum

# 2. Build and start the full stack (migrations run automatically)
docker compose up --build

# API:        http://localhost:8000
# Swagger UI: http://localhost:8000/api/docs
# ReDoc:      http://localhost:8000/api/redoc
```

## Option B — Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 15
- Redis 7

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install all dependencies including dev extras
pip install -e ".[dev]"

# 3. Copy and populate the environment file
cp .env.example .env

# 4. Apply database migrations
alembic upgrade head

# 5. Start the development server with hot-reload
uvicorn app.main:app --reload --port 8000
```

### Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy app/
```

---

# Usage

Once the server is running at `http://localhost:8000`:

- **Interactive API docs (Swagger UI):** `http://localhost:8000/api/docs`
- **ReDoc:** `http://localhost:8000/api/redoc`

### Typical Workflow

```bash
# 1. Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret", "full_name": "Ada Lovelace"}'

# 2. Login to receive tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'
# → {"access_token": "...", "refresh_token": "..."}

# 3. Create a course (use the access_token from step 2)
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Cell Biology", "description": "Intro course"}'
# → {"id": "<course_id>", ...}

# 4. Upload a study document
curl -X POST http://localhost:8000/api/v1/content/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@notes.pdf" \
  -F "course_id=<course_id>"
# → {"id": "<content_source_id>", ...}

# 5. Generate AI flashcards from the uploaded content
curl -X POST http://localhost:8000/api/v1/flashcards/generate \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"content_source_id": "<content_source_id>"}'

# 6. Open a study session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"course_id": "<course_id>"}'
# → {"id": "<session_id>", ...}

# 7. Connect to the WebSocket session for live card review
# ws://localhost:8000/api/v1/sessions/<session_id>
# Server sends: {"flashcard_id": "...", "front": "...", "back": "...", "topic": "..."}
# Client replies: {"rating": 2}   (0=Again, 1=Hard, 2=Good, 3=Easy)

# 8. Check mastery scores per topic
curl http://localhost:8000/api/v1/mastery?course_id=<course_id> \
  -H "Authorization: Bearer <access_token>"
```

### Token Refresh

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

# Error Handling

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

# Testing

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

# Future Improvements

| Area | Improvement |
|---|---|
| **Storage** | Replace `LocalStorage` with an S3-compatible adapter (the `FileStorage` ABC makes this a drop-in swap) |
| **Background tasks** | Move AI generation to a background task queue (e.g., Celery + Redis) to avoid blocking the request during large document processing |
| **Auth** | Add OAuth2 / social login providers; support multi-tenancy with organisation-scoped roles |
| **Notifications** | Push reminders when cards are due via email or WebSocket broadcast |
| **Observability** | Add structured logging (structlog), distributed tracing (OpenTelemetry), and metrics (Prometheus) |
| **Rate limiting** | Add per-user rate limiting on the AI generation endpoint to control API costs |
| **Frontend** | Build a React/Next.js client that connects to the WebSocket session for a full browser-based study experience |
| **LLM flexibility** | Extend the `AIClient` ABC with a multi-provider registry to support OpenAI, Anthropic, or local models without service-layer changes |

---

