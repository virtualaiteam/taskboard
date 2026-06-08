"""Taskboard — Kanban Board API with UI.

FastAPI + SQLite + simple HTML/JS UI. Deployed as part of the
Autonomous AI Engineering Team demo pipeline.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import Board, Column_, Card
from app.schemas import (
    BoardCreate, BoardUpdate, BoardResponse, BoardListItem,
    ColumnCreate, ColumnUpdate, ColumnResponse,
    CardCreate, CardUpdate, CardResponse,
)
from app import crud

# ── Sentry ──
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.environ.get("ENVIRONMENT", "production"),
        traces_sample_rate=0.25,
    )


# ── Lifecycle ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


# ── App ──

app = FastAPI(title="Taskboard", version="1.0.0", lifespan=lifespan)

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


# ═══════════════════════════════════════════════
# API Routes
# ═══════════════════════════════════════════════

# ── Board Endpoints ──

@app.get("/api/boards", response_model=list[BoardListItem])
def api_list_boards(db: Session = Depends(get_db)):
    return crud.list_boards(db)


@app.post("/api/boards", response_model=BoardResponse, status_code=201)
def api_create_board(data: BoardCreate, db: Session = Depends(get_db)):
    return crud.create_board(db, data)


@app.get("/api/boards/{board_id}", response_model=BoardResponse)
def api_get_board(board_id: int, db: Session = Depends(get_db)):
    board = crud.get_board(db, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@app.put("/api/boards/{board_id}", response_model=BoardResponse)
def api_update_board(board_id: int, data: BoardUpdate, db: Session = Depends(get_db)):
    board = crud.update_board(db, board_id, data)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@app.delete("/api/boards/{board_id}", status_code=204)
def api_delete_board(board_id: int, db: Session = Depends(get_db)):
    if not crud.delete_board(db, board_id):
        raise HTTPException(status_code=404, detail="Board not found")


# ── Column Endpoints ──

@app.post("/api/boards/{board_id}/columns", response_model=ColumnResponse, status_code=201)
def api_create_column(board_id: int, data: ColumnCreate, db: Session = Depends(get_db)):
    col = crud.create_column(db, board_id, data)
    if not col:
        raise HTTPException(status_code=404, detail="Board not found")
    return col


@app.put("/api/columns/{column_id}", response_model=ColumnResponse)
def api_update_column(column_id: int, data: ColumnUpdate, db: Session = Depends(get_db)):
    col = crud.update_column(db, column_id, data)
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    return col


@app.delete("/api/columns/{column_id}", status_code=204)
def api_delete_column(column_id: int, db: Session = Depends(get_db)):
    if not crud.delete_column(db, column_id):
        raise HTTPException(status_code=404, detail="Column not found")


# ── Card Endpoints ──

@app.post("/api/columns/{column_id}/cards", response_model=CardResponse, status_code=201)
def api_create_card(column_id: int, data: CardCreate, db: Session = Depends(get_db)):
    card = crud.create_card(db, column_id, data)
    if not card:
        raise HTTPException(status_code=404, detail="Column not found")
    return card


@app.put("/api/cards/{card_id}", response_model=CardResponse)
def api_update_card(card_id: int, data: CardUpdate, db: Session = Depends(get_db)):
    card = crud.update_card(db, card_id, data)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@app.delete("/api/cards/{card_id}", status_code=204)
def api_delete_card(card_id: int, db: Session = Depends(get_db)):
    if not crud.delete_card(db, card_id):
        raise HTTPException(status_code=404, detail="Card not found")


# ═══════════════════════════════════════════════
# UI Routes
# ═══════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
def ui_index(request: Request, db: Session = Depends(get_db)):
    boards = crud.list_boards(db)
    return templates.TemplateResponse(request, "index.html", {"boards": boards})


@app.get("/board/{board_id}", response_class=HTMLResponse)
def ui_board(request: Request, board_id: int, db: Session = Depends(get_db)):
    board = crud.get_board(db, board_id)
    if not board:
        return HTMLResponse("Board not found", status_code=404)
    return templates.TemplateResponse(request, "board.html", {"board": board})
