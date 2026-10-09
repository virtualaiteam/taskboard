"""Tests for the Taskboard application — models, CRUD, API, and UI routes."""
from datetime import datetime

import pytest

from app.models import Board, Column_, Card
from app.crud import (
    create_board, get_board, update_board, delete_board, list_boards,
    create_column, update_column, delete_column,
    create_card, update_card, delete_card,
)
from app.schemas import (
    BoardCreate, BoardUpdate, BoardResponse, BoardListItem,
    ColumnCreate, ColumnUpdate, ColumnResponse,
    CardCreate, CardUpdate, CardResponse,
)


# ═══════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════

class TestModels:
    def test_board_creation(self, db):
        board = Board(title="Test Board", description="A test")
        db.add(board)
        db.commit()
        db.refresh(board)
        assert board.id is not None
        assert board.title == "Test Board"
        assert board.created_at is not None

    def test_column_creation(self, db):
        board = Board(title="B")
        db.add(board)
        db.commit()
        db.refresh(board)
        col = Column_(title="To Do", position=0, board_id=board.id)
        db.add(col)
        db.commit()
        db.refresh(col)
        assert col.id is not None
        assert col.board_id == board.id

    def test_card_creation(self, db):
        board = Board(title="B")
        db.add(board)
        db.flush()
        col = Column_(title="To Do", board_id=board.id)
        db.add(col)
        db.commit()
        db.refresh(col)
        card = Card(title="Task 1", column_id=col.id)
        db.add(card)
        db.commit()
        db.refresh(card)
        assert card.id is not None
        assert card.column_id == col.id

    def test_board_column_relationship(self, db):
        board = Board(title="B")
        db.add(board)
        db.commit()
        db.refresh(board)
        for i, title in enumerate(["To Do", "Done"]):
            db.add(Column_(title=title, position=i, board_id=board.id))
        db.commit()
        assert len(board.columns) == 2

    def test_column_card_relationship(self, db):
        board = Board(title="B")
        db.add(board)
        db.flush()
        col = Column_(title="To Do", board_id=board.id)
        db.add(col)
        db.commit()
        db.refresh(col)
        for i in range(3):
            db.add(Card(title=f"Card {i}", column_id=col.id))
        db.commit()
        assert len(col.cards) == 3


# ═══════════════════════════════════════════════
# CRUD
# ═══════════════════════════════════════════════

class TestBoardCRUD:
    def test_create_board(self, db):
        board = create_board(db, BoardCreate(title="New Board", description="Desc"))
        assert board.title == "New Board"
        assert board.description == "Desc"
        assert len(board.columns) == 3  # default columns

    def test_get_board(self, db):
        board = create_board(db, BoardCreate(title="Get Me"))
        fetched = get_board(db, board.id)
        assert fetched is not None
        assert fetched.title == "Get Me"

    def test_get_board_not_found(self, db):
        assert get_board(db, 9999) is None

    def test_update_board(self, db):
        board = create_board(db, BoardCreate(title="Old"))
        updated = update_board(db, board.id, BoardUpdate(title="New"))
        assert updated.title == "New"

    def test_update_board_none_fields(self, db):
        board = create_board(db, BoardCreate(title="Old", description="Desc"))
        updated = update_board(db, board.id, BoardUpdate(title=None))
        assert updated.title == "Old"

    def test_update_board_not_found(self, db):
        assert update_board(db, 9999, BoardUpdate(title="X")) is None

    def test_delete_board(self, db):
        board = create_board(db, BoardCreate(title="Delete Me"))
        assert delete_board(db, board.id) is True
        assert get_board(db, board.id) is None

    def test_delete_board_not_found(self, db):
        assert delete_board(db, 9999) is False

    def test_list_boards(self, db):
        create_board(db, BoardCreate(title="Board A"))
        create_board(db, BoardCreate(title="Board B"))
        boards = list_boards(db)
        assert len(boards) == 2

    def test_create_board_cascades_columns(self, db):
        board = create_board(db, BoardCreate(title="Cascaded"))
        assert len(board.columns) == 3
        titles = [c.title for c in board.columns]
        assert "To Do" in titles
        assert "In Progress" in titles
        assert "Done" in titles


class TestColumnCRUD:
    def test_create_column(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col = create_column(db, board.id, ColumnCreate(title="Review", position=3))
        assert col.title == "Review"
        assert col.position == 3
        assert col.board_id == board.id

    def test_create_column_board_not_found(self, db):
        assert create_column(db, 9999, ColumnCreate(title="X")) is None

    def test_update_column(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col = create_column(db, board.id, ColumnCreate(title="Old"))
        updated = update_column(db, col.id, ColumnUpdate(title="New"))
        assert updated.title == "New"

    def test_delete_column(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col = create_column(db, board.id, ColumnCreate(title="Del"))
        assert delete_column(db, col.id) is True
        assert db.query(Column_).filter(Column_.id == col.id).first() is None


class TestCardCRUD:
    def test_create_card(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        card = create_card(db, col.id, CardCreate(title="Do stuff"))
        assert card.title == "Do stuff"
        assert card.column_id == col.id
        assert card.position == 0

    def test_create_card_auto_position(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        create_card(db, col.id, CardCreate(title="Card 1"))
        card2 = create_card(db, col.id, CardCreate(title="Card 2"))
        assert card2.position == 1

    def test_update_card(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        card = create_card(db, col.id, CardCreate(title="Old"))
        updated = update_card(db, card.id, CardUpdate(title="New", description="Desc"))
        assert updated.title == "New"
        assert updated.description == "Desc"

    def test_update_card_move_column(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col1 = create_column(db, board.id, ColumnCreate(title="To Do"))
        col2 = create_column(db, board.id, ColumnCreate(title="Done"))
        card = create_card(db, col1.id, CardCreate(title="Move me"))
        updated = update_card(db, card.id, CardUpdate(column_id=col2.id))
        assert updated.column_id == col2.id

    def test_delete_card(self, db):
        board = create_board(db, BoardCreate(title="B"))
        col = create_column(db, board.id, ColumnCreate(title="To Do"))
        card = create_card(db, col.id, CardCreate(title="Del"))
        assert delete_card(db, card.id) is True


# ═══════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════

class TestSchemas:
    def test_board_create_valid(self):
        data = BoardCreate(title="Valid")
        assert data.title == "Valid"
        assert data.description == ""

    def test_board_create_empty_title(self):
        with pytest.raises(Exception):
            BoardCreate(title="")

    def test_board_update_optional_fields(self):
        data = BoardUpdate(description="Only desc")
        assert data.title is None
        assert data.description == "Only desc"

    def test_card_response_from_attributes(self):
        assert "from_attributes" in CardResponse.model_config

    def test_column_response_from_attributes(self):
        assert "from_attributes" in ColumnResponse.model_config

    def test_board_response_from_attributes(self):
        assert "from_attributes" in BoardResponse.model_config

    def test_card_update_optional_all_fields(self):
        data = CardUpdate(title="T", description="D", column_id=1, position=5)
        assert data.title == "T"
        assert data.column_id == 1
        assert data.position == 5

    def test_board_list_item(self):
        data = BoardListItem(id=1, title="T", description="D",
                             created_at=datetime(2024, 1, 1))
        assert data.id == 1
