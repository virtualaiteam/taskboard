# Taskboard — Project Review

## Architecture Overview

Taskboard is a Kanban Board demo application built as part of the **Autonomous AI Engineering Team** pipeline. It provides a full RESTful API and a server-rendered HTML/JS frontend for managing Kanban boards with columns and cards.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12) |
| Database | SQLite (file-based, zero configuration) |
| ORM | SQLAlchemy 2.0+ |
| Validation | Pydantic v2 |
| Templating | Jinja2 |
| Error Tracking | Sentry SDK |
| Deployment | Docker Compose / Uvicorn |

### Project Structure

```
taskboard/
├── app/
│   ├── main.py          # FastAPI application, routes (API + UI)
│   ├── models.py        # SQLAlchemy ORM models (Board, Column_, Card)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database CRUD operations
│   ├── database.py      # SQLAlchemy engine, session, Base
│   └── templates/
│       ├── index.html   # Board listing page
│       └── board.html   # Kanban board view with drag-and-drop
├── tests/               # Pytest test suite
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container build definition
├── docker-compose.yml   # Docker Compose orchestration
└── taskboard.db         # SQLite database (runtime)
```

### Core Models

Three SQLAlchemy models form the data layer:

- **Board** — Top-level container with `id`, `title`, `description`, `created_at`, `updated_at`. Has a one-to-many relationship with `Column_`.
- **Column_** — Represents a Kanban column with `id`, `title`, `position`, `board_id`. Contains a one-to-many relationship with `Card`. The underscore in the name avoids conflict with Python's `column` keyword.
- **Card** — Individual task items with `id`, `title`, `description`, `position`, `column_id`.

Cascade delete-orphan rules ensure that deleting a board removes all its columns and cards.

### API Design

The API follows REST conventions with JSON request/response bodies:

- **Boards:** `GET/POST /api/boards`, `GET/PUT/DELETE /api/boards/{id}`
- **Columns:** `POST /api/boards/{id}/columns`, `PUT/DELETE /api/columns/{id}`
- **Cards:** `POST /api/columns/{id}/cards`, `PUT/DELETE /api/cards/{id}`

All endpoints use Pydantic schemas for input validation and response serialization. The `from_attributes` config enables Pydantic to read from SQLAlchemy ORM objects.

### Frontend Integration

Jinja2 templates provide server-rendered HTML:

- **`/`** — Lists all boards (via `ui_index`), rendered from `index.html`
- **`/board/{id}`** — Shows a single Kanban board (via `ui_board`), rendered from `board.html`

The frontend uses vanilla JavaScript for:
- Modal-based create/edit forms for boards, columns, and cards
- Drag-and-drop card movement between columns (native HTML5 DnD API)
- Fetch API calls to the REST endpoints
- Optimistic UI updates with rollback on failure

### Data Flow

```
User → Browser (Jinja2 template + JS) → FastAPI routes → CRUD layer → SQLAlchemy → SQLite
```

The `lifespan` context manager initializes the database tables on startup via `init_db()`, which calls `Base.metadata.create_all()`.

### Error Tracking

Sentry SDK is initialized from the `SENTRY_DSN` environment variable. When set, it captures errors and sends them to sentry.io with a 25% trace sampling rate.

## Project Setup

### Docker

The application runs in a container based on `python:3.12-slim`:

```bash
docker compose up -d
```

This builds the image, exposes port 8001 (mapped to container port 8000), and mounts a named volume for persistent SQLite data. Sentry integration is configured via environment variables.

### Requirements

Install dependencies directly (no virtual environment needed when using the pre-installed environment):

```bash
pip install -r requirements.txt
```

Dependencies:

| Package | Purpose |
|---------|---------|
| fastapi>=0.115.0 | Web framework |
| uvicorn[standard]>=0.32.0 | ASGI server |
| sqlalchemy>=2.0.0 | ORM and database layer |
| sentry-sdk>=2.0.0 | Error tracking |
| jinja2>=3.1.0 | Template engine |
| pydantic>=2.0.0 | Data validation |
| python-multipart>=0.0.17 | Form data parsing |

### Running Manually

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The database file `taskboard.db` is created automatically on first startup.
