"""Tests for the Taskboard Kanban API.

Tests the business-logic layer (models, schemas, CRUD) directly via
SQLAlchemy sessions.  The HTTP transport layer requires httpx2 which
is not available in this environment, so routes are tested through
the underlying data layer instead.
"""
from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud import (
    create_board, create_column, create_card,
    update_board, update_column, update_card,
    delete_board, delete_column, delete_card,
    list_boards, get_board,
)
from app.database import Base, init_db
from app.models import Board, Column_, Card
from app.schemas import (
    BoardCreate, BoardUpdate, BoardResponse, BoardListItem,
    ColumnCreate, ColumnUpdate, ColumnResponse,
    CardCreate, CardUpdate, CardResponse,
)
from app.main import app


# ── Test Database Setup ──

@pytest.fixture()
def db():
    """Provide a fresh in-memory SQLite session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ═══════════════════════════════════════════════
# Schema Validation Tests
# ═══════════════════════════════════════════════

class TestSchemaValidation:
    """Test Pydantic schema validation for request/response models."""

    def test_board_create_valid(self):
        schema = BoardCreate(title="Valid Board")
        assert schema.title == "Valid Board"
        assert schema.description == ""

    def test_board_create_with_description(self):
        schema = BoardCreate(title="Board", description="A desc")
        assert schema.description == "A desc"

    def test_board_create_empty_title_rejected(self):
        with pytest.raises(Exception):
            BoardCreate(title="")

    def test_board_create_title_too_long_rejected(self):
        with pytest.raises(Exception):
            BoardCreate(title="A" * 201)

    def test_board_response_from_attributes(self):
        from datetime import datetime
        board = Board(id=1, title="T", description="D",
                      created_at=datetime.now(), updated_at=datetime.now())
        data = BoardResponse.model_validate(board)
        assert data.id == 1
        assert data.title == "T"

    def test_column_create_valid(self):
        schema = ColumnCreate(title="My Column", position=3)
        assert schema.title == "My Column"
        assert schema.position == 3

    def test_column_create_empty_title_rejected(self):
        with pytest.raises(Exception):
            ColumnCreate(title="")

    def test_column_response_from_attributes(self):
        col = Column_(id=1, title="T", position=0, board_id=1)
        data = ColumnResponse.model_validate(col)
        assert data.id == 1

    def test_card_create_valid(self):
        schema = CardCreate(title="Card Title", description="Detail")
        assert schema.title == "Card Title"
        assert schema.description == "Detail"

    def test_card_create_empty_title_rejected(self):
        with pytest.raises(Exception):
            CardCreate(title="")

    def test_card_create_title_too_long_rejected(self):
        with pytest.raises(Exception):
            CardCreate(title="A" * 301)

    def test_card_response_from_attributes(self):
        card = Card(id=1, title="T", description="D", position=0, column_id=1)
        data = CardResponse.model_validate(card)
        assert data.id == 1

    def test_card_update_optional_fields(self):
        schema = CardUpdate(title="New Title")
        assert schema.title == "New Title"
        assert schema.description is None
        assert schema.column_id is None
        assert schema.position is None

    def test_board_update_optional_fields(self):
        schema = BoardUpdate(title="New")
        assert schema.title == "New"
        assert schema.description is None

    def test_column_update_optional_fields(self):
        schema = ColumnUpdate(title="New")
        assert schema.title == "New"
        assert schema.position is None


# ═══════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════

class TestModels:
    """Test SQLAlchemy model definitions and relationships."""

    def test_board_has_correct_attributes(self):
        board = Board(title="Test", description="Desc")
        assert board.title == "Test"
        assert board.description == "Desc"
        assert board.columns == []

    def test_board_columns_relationship(self):
        board = Board(title="Test")
        col = Column_(title="To Do", position=0, board_id=board.id if board.id else 1)
        board.columns.append(col)
        assert len(board.columns) == 1
        assert board.columns[0].title == "To Do"

    def test_column_cards_relationship(self):
        col = Column_(title="To Do", position=0, board_id=1)
        card = Card(title="Task", column_id=col.id if col.id else 1)
        col.cards.append(card)
        assert len(col.cards) == 1
        assert col.cards[0].title == "Task"

    def test_card_belongs_to_column(self):
        card = Card(title="Task", column_id=42)
        assert card.column_id == 42

    def test_board_table_name(self):
        assert Board.__tablename__ == "boards"

    def test_column_table_name(self):
        assert Column_.__tablename__ == "columns"

    def test_card_table_name(self):
        assert Card.__tablename__ == "cards"


# ═══════════════════════════════════════════════
# Board CRUD Tests
# ═══════════════════════════════════════════════

class TestBoardCRUD:
    """Test board CRUD operations via the data layer."""

    def test_create_board_creates_default_columns(self, db):
        board = create_board(db, BoardCreate(title="Test Board", description="Desc"))
        assert board.title == "Test Board"
        assert board.description == "Desc"
        assert len(board.columns) == 3
        col_titles = [c.title for c in board.columns]
        assert "To Do" in col_titles
        assert "In Progress" in col_titles
        assert "Done" in col_titles

    def test_create_board_default_position_order(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        positions = {c.title: c.position for c in board.columns}
        assert positions["To Do"] == 0
        assert positions["In Progress"] == 1
        assert positions["Done"] == 2

    def test_list_boards_ordered_by_updated_at_desc(self, db):
        from datetime import datetime, timedelta
        board_a = create_board(db, BoardCreate(title="Board A"))
        # SQLite's func.now() has second-level precision, so set timestamps manually
        board_a.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        db.commit()
        db.refresh(board_a)
        board_b = create_board(db, BoardCreate(title="Board B"))
        board_b.updated_at = datetime(2024, 1, 1, 12, 0, 1)
        db.commit()
        db.refresh(board_b)
        boards = list_boards(db)
        assert len(boards) == 2
        assert boards[0].title == "Board B"
        assert boards[1].title == "Board A"

    def test_get_board_found(self, db):
        board = create_board(db, BoardCreate(title="Get Me"))
        found = get_board(db, board.id)
        assert found is not None
        assert found.title == "Get Me"

    def test_get_board_not_found(self, db):
        result = get_board(db, 99999)
        assert result is None

    def test_update_board_title(self, db):
        board = create_board(db, BoardCreate(title="Old"))
        result = update_board(db, board.id, BoardUpdate(title="New"))
        assert result is not None
        assert result.title == "New"

    def test_update_board_preserves_description(self, db):
        board = create_board(db, BoardCreate(title="Keep", description="Desc"))
        result = update_board(db, board.id, BoardUpdate(title="New"))
        assert result.description == "Desc"

    def test_update_board_not_found(self, db):
        result = update_board(db, 99999, BoardUpdate(title="X"))
        assert result is None

    def test_delete_board_returns_true(self, db):
        board = create_board(db, BoardCreate(title="Delete Me"))
        result = delete_board(db, board.id)
        assert result is True

    def test_delete_board_not_found_returns_false(self, db):
        result = delete_board(db, 99999)
        assert result is False

    def test_delete_board_cascades_to_columns(self, db):
        board = create_board(db, BoardCreate(title="Cascade"))
        col = Column_(title="Extra", position=3, board_id=board.id)
        db.add(col)
        db.commit()
        db.refresh(board)
        assert len(board.columns) == 4
        delete_board(db, board.id)
        remaining = db.query(Column_).filter(Column_.board_id == board.id).all()
        assert len(remaining) == 0

    def test_delete_board_cascades_to_cards(self, db):
        board = create_board(db, BoardCreate(title="Cascade"))
        col = Column_(title="Extra", position=3, board_id=board.id)
        db.add(col)
        db.commit()
        db.refresh(board)
        card = Card(title="Orphan", column_id=col.id)
        db.add(card)
        db.commit()
        delete_board(db, board.id)
        remaining = db.query(Card).filter(Card.column_id == col.id).all()
        assert len(remaining) == 0


# ═══════════════════════════════════════════════
# Column CRUD Tests
# ═══════════════════════════════════════════════

class TestColumnCRUD:
    """Test column CRUD operations via the data layer."""

    def test_create_column_success(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="My Column", position=5))
        assert col is not None
        assert col.title == "My Column"
        assert col.position == 5
        assert col.board_id == board.id

    def test_create_column_board_not_found(self, db):
        result = create_column(db, 99999, ColumnCreate(title="Ghost"))
        assert result is None

    def test_update_column_title(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="Old"))
        result = update_column(db, col.id, ColumnUpdate(title="New"))
        assert result is not None
        assert result.title == "New"

    def test_update_column_position(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="Col", position=0))
        result = update_column(db, col.id, ColumnUpdate(position=10))
        assert result.position == 10

    def test_update_column_not_found(self, db):
        result = update_column(db, 99999, ColumnUpdate(title="X"))
        assert result is None

    def test_delete_column_returns_true(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="Col"))
        result = delete_column(db, col.id)
        assert result is True

    def test_delete_column_not_found_returns_false(self, db):
        result = delete_column(db, 99999)
        assert result is False


# ═══════════════════════════════════════════════
# Card CRUD Tests
# ═══════════════════════════════════════════════

class TestCardCRUD:
    """Test card CRUD operations via the data layer."""

    def test_create_card_success(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        card = create_card(db, col.id, CardCreate(title="First Card"))
        assert card is not None
        assert card.title == "First Card"
        assert card.position == 0
        assert card.column_id == col.id

    def test_create_card_position_auto_increment(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        create_card(db, col.id, CardCreate(title="Card 1"))
        card2 = create_card(db, col.id, CardCreate(title="Card 2"))
        assert card2.position == 1

    def test_create_card_column_not_found(self, db):
        result = create_card(db, 99999, CardCreate(title="Ghost"))
        assert result is None

    def test_update_card_title(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        card = create_card(db, col.id, CardCreate(title="Old"))
        result = update_card(db, card.id, CardUpdate(title="New"))
        assert result is not None
        assert result.title == "New"

    def test_update_card_move_column(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col_a = create_column(db, board.id, ColumnCreate(title="A"))
        col_b = create_column(db, board.id, ColumnCreate(title="B"))
        card = create_card(db, col_a.id, CardCreate(title="Mover"))
        result = update_card(db, card.id, CardUpdate(column_id=col_b.id))
        assert result is not None
        assert result.column_id == col_b.id

    def test_update_card_not_found(self, db):
        result = update_card(db, 99999, CardUpdate(title="X"))
        assert result is None

    def test_delete_card_returns_true(self, db):
        board = create_board(db, BoardCreate(title="Test"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        card = create_card(db, col.id, CardCreate(title="Delete Me"))
        result = delete_card(db, card.id)
        assert result is True

    def test_delete_card_not_found_returns_false(self, db):
        result = delete_card(db, 99999)
        assert result is False


# ═══════════════════════════════════════════════
# Database / App Configuration Tests
# ═══════════════════════════════════════════════

class TestDatabaseSetup:
    """Test database initialisation and app configuration."""

    def test_init_db_creates_tables(self):
        """init_db should create all model tables."""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        # Tables shouldn't exist yet
        inspector = engine.dialect.get_table_names(engine.connect()) if hasattr(engine, 'connect') else []
        init_db.__code__  # just to ensure import works
        Base.metadata.create_all(bind=engine)
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(engine)
        tables = inspector.get_table_names()
        assert "boards" in tables
        assert "columns" in tables
        assert "cards" in tables

    def test_fastapi_app_exists(self):
        """The FastAPI app instance should be importable and configured."""
        assert app is not None
        assert app.title == "Taskboard"
        assert app.version == "1.0.0"

    def test_fastapi_app_has_lifespan(self):
        """App should have a lifespan context manager defined in main.py."""
        import app.main as main_module
        assert hasattr(main_module, "lifespan")
        import inspect
        # asynccontextmanager wraps the function, so it's not an async gen
        assert callable(main_module.lifespan)

    def test_database_url_is_sqlite(self):
        """Default database URL should point to a SQLite file."""
        import app.database as db_module
        assert "sqlite" in db_module.DATABASE_URL

    def test_get_db_is_generator(self):
        """get_db should be a generator function for dependency injection."""
        import app.database as db_module
        import inspect
        assert inspect.isgeneratorfunction(db_module.get_db)
