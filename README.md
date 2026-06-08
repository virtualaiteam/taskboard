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
- **UI:** Server-rendered HTML + vanilla JS + CSS
- **Error Tracking:** Sentry SDK
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
