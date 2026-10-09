# Taskboard — Kanban Board Demo App

A Kanban Board API with a modern UI, built as a demo for the **Autonomous AI Engineering Team** pipeline.

**Live demo:** http://192.168.0.13:8000 → UI available on your LAN  
**GitHub:** https://github.com/virtualaiteam/taskboard  
**Error tracking:** Sentry — project `python-fastapi` under `ididify` org

## Features

- ✅ Multiple Kanban boards
- ✅ Drag-and-drop cards between columns
- ✅ Add/Edit/Delete boards, columns, and cards
- ✅ Sentry error tracking integrated
- ✅ RESTful API
- ✅ Docker deployment
- ✅ Machine-First Architecture — full traceability from bug → ticket → fix → deploy

## Tech Stack

- **Backend:** FastAPI (Python 3.12)
- **Database:** SQLite (file-based, zero config)
- **ORM:** SQLAlchemy 2.0+ (declarative models)
- **Validation:** Pydantic v2 (request/response schemas)
- **UI:** Server-rendered HTML + vanilla JS + CSS (htmx.org)
- **Error Tracking:** Sentry SDK
- **Server:** Uvicorn (ASGI)
- **Deployment:** Docker Compose

## Quick Start

```bash
# Clone
git clone https://github.com/virtualaiteam/taskboard.git
cd taskboard

# Run with Docker
docker compose up -d

# Or without Docker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/boards` | List all boards |
| POST | `/api/boards` | Create a board |
| GET | `/api/boards/{id}` | Get board with columns and cards |
| PUT | `/api/boards/{id}` | Update board |
| DELETE | `/api/boards/{id}` | Delete board |
| POST | `/api/boards/{id}/columns` | Add a column |
| PUT | `/api/columns/{id}` | Update column |
| DELETE | `/api/columns/{id}` | Delete column |
| POST | `/api/columns/{id}/cards` | Add a card |
| PUT | `/api/cards/{id}` | Update card (title, desc, move column) |
| DELETE | `/api/cards/{id}` | Delete card |

## Architecture

```
User → Browser (UI) → FastAPI → SQLite
                         ↓
                     Sentry SDK → sentry.io
                         ↓
                Monitor Agent → Plane Ticket
                         ↓
                Engineer Agent → Fix → Deploy
```

### Project Structure

```
taskboard/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, routes (API + UI), lifespan
│   ├── models.py        # SQLAlchemy ORM models (Board, Column_, Card)
│   ├── schemas.py       # Pydantic v2 request/response schemas
│   ├── crud.py          # CRUD operations (business logic)
│   ├── database.py      # SQLAlchemy engine, session, Base
│   └── templates/
│       ├── index.html   # Board list page
│       └── board.html   # Kanban board view with drag-and-drop
├── tests/
│   └── test_app.py      # 54 pytest tests (schemas, models, CRUD)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### Layered Design

The codebase follows a clean layered architecture:

1. **Routes** (`main.py`) — HTTP layer. Defines API endpoints and UI templates. Delegates all business logic to the CRUD layer.
2. **CRUD** (`crud.py`) — Business logic layer. Pure functions that operate on SQLAlchemy sessions. No HTTP knowledge.
3. **Models** (`models.py`) — Domain entities. SQLAlchemy declarative models with relationships and cascade rules.
4. **Schemas** (`schemas.py`) — Data contracts. Pydantic v2 models for request validation and response serialization.
5. **Database** (`database.py`) — Infrastructure. Engine configuration, session factory, table creation.

### Data Model

```
Board (1) ──< (N) Column_ (1) ──< (N) Card
```

- **Board**: `id`, `title`, `description`, `created_at`, `updated_at`
- **Column_**: `id`, `title`, `position`, `board_id` (FK → boards)
- **Card**: `id`, `title`, `description`, `position`, `column_id` (FK → columns)

Cascade rules: deleting a board deletes all its columns and cards. Deleting a column deletes all its cards.

## Autonomous Pipeline

This app demonstrates the full **bug → detection → fix → deploy** pipeline:

1. **App reports errors** to Sentry via SDK
2. **Monitor Agent** polls Sentry every 60s
3. **New error detected** → Plane bug ticket auto-created
4. **Orchestrator** assigns engineer agent
5. **Engineer fixes** → commits → deploys
6. **Monitor Agent** verifies error resolved

## Demo Credentials

No authentication required — this is a demo app. All data is stored in SQLite at `/app/data/taskboard.db` inside the container.
