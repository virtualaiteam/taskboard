# Project Review: Taskboard — Kanban Board Demo App

## Architecture Overview

Taskboard is a full-stack Kanban board application built as a demonstration for the **Autonomous AI Engineering Team** pipeline. It follows a clean, layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│  UI Layer (Jinja2 + HTMX + vanilla JS) │
├─────────────────────────────────────────┤
│  Route Layer (FastAPI endpoints)        │
├─────────────────────────────────────────┤
│  Schema Layer (Pydantic v2 models)      │
├─────────────────────────────────────────┤
│  CRUD Layer (business logic)            │
├─────────────────────────────────────────┤
│  ORM Layer (SQLAlchemy models)          │
├─────────────────────────────────────────┤
│  Database (SQLite)                      │
└─────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Web Framework | FastAPI | >= 0.115.0 |
| ASGI Server | Uvicorn | >= 0.32.0 |
| ORM | SQLAlchemy | >= 2.0.0 |
| Validation | Pydantic | >= 2.0.0 |
| Templating | Jinja2 | >= 3.1.0 |
| Error Tracking | Sentry SDK | >= 2.0.0 |
| Form Handling | python-multipart | >= 0.0.17 |
| Runtime | Python 3.12 | — |

## Project Structure

```
taskboard/
├── app/
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI app, routes, lifespan
│   ├── database.py          # Engine, session, Base
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── crud.py              # Database operations
│   └── templates/
│       ├── index.html       # Board list page
│       └── board.html       # Kanban board page
├── tests/
│   ├── conftest.py          # Fixtures, in-memory DB setup
│   └── test_app.py          # 46 unit tests
├── requirements.txt         # Dependencies
├── Dockerfile               # Container build
├── docker-compose.yml       # Docker Compose deployment
└── README.md                # Documentation
```

## Key Design Decisions

### 1. In-Memory SQLite
The database uses SQLite with `check_same_thread=False`, making it suitable for single-process deployments. The file-based approach means zero configuration — ideal for demos and small teams.

### 2. Default Columns on Board Creation
When a board is created via `crud.create_board()`, three default columns ("To Do", "In Progress", "Done") are automatically seeded. This gives users an immediate, usable board without extra setup.

### 3. Cascade Deletes
SQLAlchemy relationships use `cascade="all, delete-orphan"` on both Board→Column and Column→Card, ensuring referential integrity. Deleting a board removes all its columns and cards.

### 4. Auto-Positioning for Cards
New cards are positioned after the last card in their column using a `MAX(position)` query, so manual position assignment is not required.

### 5. HTMX for Interactivity
The UI leverages HTMX (loaded from CDN) for dynamic interactions, reducing the need for a heavy JavaScript framework. The board page uses vanilla JS for drag-and-drop functionality.

### 6. Sentry Error Tracking
Sentry is conditionally initialized when the `SENTRY_DSN` environment variable is set, enabling production error tracking without impacting local development.

## Assessment

### Strengths
- **Clean separation of concerns**: Models, schemas, CRUD, and routes are in separate files
- **Comprehensive CRUD**: Full create/read/update/delete for boards, columns, and cards
- **Good schema validation**: Pydantic schemas enforce field lengths and types
- **Cascading deletes**: Proper relational integrity at the ORM level
- **Docker support**: Clean Dockerfile and docker-compose.yml for deployment
- **Test coverage**: 46 tests covering CRUD operations, schema validation, and model relationships using in-memory SQLite
- **Modern stack**: FastAPI, SQLAlchemy 2.0, Pydantic v2

### Observations
- **No authentication**: The README acknowledges this is a demo app without auth — appropriate for the stated purpose
- **External CDN dependency**: HTMX and Google Fonts are loaded from external CDNs, which could be a concern in air-gapped environments
- **No API versioning**: Routes use flat paths (`/api/boards`) without version prefixes
- **Sentry DSN in docker-compose.yml**: The DSN is hardcoded in the compose file, which is a minor security concern for a public repo (though the DSN appears to be a read-only endpoint key)

### Recommendations
1. **Consider adding an API version prefix** (e.g., `/api/v1/...`) for future compatibility
2. **Add rate limiting** if the app is exposed to untrusted users
3. **Pin dependency versions** in requirements.txt for reproducible builds
4. **Add a health check endpoint** (e.g., `GET /health`) for Docker monitoring
5. **Consider a migration tool** (e.g., Alembic) if the schema is expected to evolve

## Test Summary

| Category | Tests | Status |
|----------|-------|--------|
| Board CRUD | 11 | Pass |
| Column CRUD | 6 | Pass |
| Card CRUD | 8 | Pass |
| Schema Validation | 14 | Pass |
| Model Definitions | 7 | Pass |
| **Total** | **46** | **All Pass** |

Tests use an in-memory SQLite database with automatic table creation and teardown via pytest fixtures, ensuring isolation between test cases.
