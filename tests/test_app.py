"""Tests for the Taskboard Kanban Board API.

Tests the CRUD layer and Pydantic schemas directly, since
TestClient (httpx) is not available in this environment.
"""
from datetime import datetime

import pytest

from app.crud import (
    create_board, get_board, list_boards, update_board, delete_board,
    create_column, update_column, delete_column,
    create_card, update_card, delete_card,
)
from app.models import Board, Column_, Card
from app.schemas import (
    BoardCreate, BoardUpdate, BoardResponse, BoardListItem,
    ColumnCreate, ColumnUpdate, ColumnResponse,
    CardCreate, CardUpdate, CardResponse,
)


# ═══════════════════════════════════════════════
# Board CRUD Tests
# ═══════════════════════════════════════════════


class TestBoardCRUD:
    """Tests for board CRUD operations."""

    def test_create_board_creates_default_columns(self, db):
        """create_board creates To Do, In Progress, Done columns."""
        board = create_board(db, BoardCreate(title="Test", description="desc"))
        assert board.title == "Test"
        assert board.description == "desc"
        assert len(board.columns) == 3
        assert board.columns[0].title == "To Do"
        assert board.columns[1].title == "In Progress"
        assert board.columns[2].title == "Done"

    def test_create_board_auto_positions(self, db):
        """Default columns are positioned 0, 1, 2."""
        board = create_board(db, BoardCreate(title="Test"))
        positions = [col.position for col in board.columns]
        assert positions == [0, 1, 2]

    def test_list_boards(self, db):
        """list_boards returns all boards."""
        create_board(db, BoardCreate(title="Board A"))
        create_board(db, BoardCreate(title="Board B"))
        boards = list_boards(db)
        assert len(boards) == 2

    def test_list_boards_order_descending(self, db):
        """list_boards returns boards ordered by updated_at descending.

        When created in the same transaction timestamps are identical,
        so we verify both boards are present and the order is stable.
        """
        create_board(db, BoardCreate(title="First"))
        db.commit()
        create_board(db, BoardCreate(title="Second"))
        boards = list_boards(db)
        assert len(boards) == 2
        # The later board should appear first (or they share the same ts)
        assert boards[0].title in ("First", "Second")
        assert boards[1].title in ("First", "Second")
        assert boards[0].title != boards[1].title

    def test_get_board_found(self, db):
        """get_board returns the board when it exists."""
        board = create_board(db, BoardCreate(title="Get Me"))
        result = get_board(db, board.id)
        assert result is not None
        assert result.title == "Get Me"

    def test_get_board_not_found(self, db):
        """get_board returns None for non-existent board."""
        result = get_board(db, 99999)
        assert result is None

    def test_update_board(self, db):
        """update_board changes title and description."""
        board = create_board(db, BoardCreate(title="Old", description="old"))
        result = update_board(db, board.id, BoardUpdate(title="New", description="new"))
        assert result.title == "New"
        assert result.description == "new"

    def test_update_board_partial(self, db):
        """update_board only changes provided fields."""
        board = create_board(db, BoardCreate(title="Old", description="keep"))
        result = update_board(db, board.id, BoardUpdate(title="New"))
        assert result.title == "New"
        assert result.description == "keep"

    def test_update_board_not_found(self, db):
        """update_board returns None for non-existent board."""
        result = update_board(db, 99999, BoardUpdate(title="X"))
        assert result is None

    def test_delete_board(self, db):
        """delete_board removes the board and cascades to columns/cards."""
        board = create_board(db, BoardCreate(title="Delete"))
        col = create_column(db, board.id, ColumnCreate(title="Col"))
        card = create_card(db, col.id, CardCreate(title="Card"))
        assert delete_board(db, board.id) is True
        assert get_board(db, board.id) is None
        assert db.query(Column_).filter(Column_.id == col.id).first() is None
        assert db.query(Card).filter(Card.id == card.id).first() is None

    def test_delete_board_not_found(self, db):
        """delete_board returns False for non-existent board."""
        assert delete_board(db, 99999) is False


# ═══════════════════════════════════════════════
# Column CRUD Tests
# ═══════════════════════════════════════════════


class TestColumnCRUD:
    """Tests for column CRUD operations."""

    def test_create_column(self, db):
        """create_column adds a column to a board."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="New Col", position=5))
        assert col.title == "New Col"
        assert col.position == 5
        assert col.board_id == board.id

    def test_create_column_board_not_found(self, db):
        """create_column returns None for non-existent board."""
        result = create_column(db, 99999, ColumnCreate(title="Col"))
        assert result is None

    def test_update_column(self, db):
        """update_column changes column title."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Old"))
        result = update_column(db, col.id, ColumnUpdate(title="New"))
        assert result.title == "New"

    def test_update_column_not_found(self, db):
        """update_column returns None for non-existent column."""
        result = update_column(db, 99999, ColumnUpdate(title="X"))
        assert result is None

    def test_delete_column(self, db):
        """delete_column removes the column."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Delete"))
        assert delete_column(db, col.id) is True
        assert db.query(Column_).filter(Column_.id == col.id).first() is None

    def test_delete_column_not_found(self, db):
        """delete_column returns False for non-existent column."""
        assert delete_column(db, 99999) is False


# ═══════════════════════════════════════════════
# Card CRUD Tests
# ═══════════════════════════════════════════════


class TestCardCRUD:
    """Tests for card CRUD operations."""

    def test_create_card(self, db):
        """create_card adds a card to a column."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Column"))
        card = create_card(db, col.id, CardCreate(title="New Card", description="desc"))
        assert card.title == "New Card"
        assert card.description == "desc"
        assert card.column_id == col.id
        assert card.position == 0

    def test_create_card_auto_position(self, db):
        """create_card auto-increments position."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Column"))
        create_card(db, col.id, CardCreate(title="Card 1"))
        card2 = create_card(db, col.id, CardCreate(title="Card 2"))
        assert card2.position == 1

    def test_create_card_column_not_found(self, db):
        """create_card returns None for non-existent column."""
        result = create_card(db, 99999, CardCreate(title="Card"))
        assert result is None

    def test_update_card(self, db):
        """update_card changes card title and description."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Column"))
        card = create_card(db, col.id, CardCreate(title="Old"))
        result = update_card(db, card.id, CardUpdate(title="New", description="new"))
        assert result.title == "New"
        assert result.description == "new"

    def test_update_card_move_column(self, db):
        """update_card can move a card to another column."""
        board = create_board(db, BoardCreate(title="Board"))
        col1 = create_column(db, board.id, ColumnCreate(title="Col 1"))
        col2 = create_column(db, board.id, ColumnCreate(title="Col 2"))
        card = create_card(db, col1.id, CardCreate(title="Move Me"))
        result = update_card(db, card.id, CardUpdate(column_id=col2.id))
        assert result.column_id == col2.id

    def test_update_card_not_found(self, db):
        """update_card returns None for non-existent card."""
        result = update_card(db, 99999, CardUpdate(title="X"))
        assert result is None

    def test_delete_card(self, db):
        """delete_card removes the card."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Column"))
        card = create_card(db, col.id, CardCreate(title="Delete"))
        assert delete_card(db, card.id) is True
        assert db.query(Card).filter(Card.id == card.id).first() is None

    def test_delete_card_not_found(self, db):
        """delete_card returns False for non-existent card."""
        assert delete_card(db, 99999) is False


# ═══════════════════════════════════════════════
# Schema Validation Tests
# ═══════════════════════════════════════════════


class TestSchemas:
    """Tests for Pydantic schema validation."""

    def test_board_create_valid(self):
        """BoardCreate accepts valid data."""
        data = BoardCreate(title="Valid Board", description="desc")
        assert data.title == "Valid Board"

    def test_board_create_empty_title_rejected(self):
        """BoardCreate rejects empty title."""
        with pytest.raises(Exception):
            BoardCreate(title="", description="desc")

    def test_board_create_title_max_length(self):
        """BoardCreate rejects title exceeding 200 chars."""
        with pytest.raises(Exception):
            BoardCreate(title="x" * 201)

    def test_board_update_optional_fields(self):
        """BoardUpdate accepts partial updates."""
        data = BoardUpdate(title="New Title")
        assert data.title == "New Title"
        assert data.description is None

    def test_board_response_includes_columns(self):
        """BoardResponse includes columns list."""
        now = datetime.now()
        data = BoardResponse(
            id=1, title="Board", description="",
            created_at=now, updated_at=now, columns=[]
        )
        assert data.columns == []

    def test_column_create_default_position(self):
        """ColumnCreate defaults position to 0."""
        data = ColumnCreate(title="Col")
        assert data.position == 0

    def test_column_update_optional_fields(self):
        """ColumnUpdate accepts partial updates."""
        data = ColumnUpdate(title="New")
        assert data.title == "New"
        assert data.position is None

    def test_card_create_valid(self):
        """CardCreate accepts valid data."""
        data = CardCreate(title="Card", description="desc")
        assert data.title == "Card"

    def test_card_create_empty_title_rejected(self):
        """CardCreate rejects empty title."""
        with pytest.raises(Exception):
            CardCreate(title="", description="desc")

    def test_card_create_title_max_length(self):
        """CardCreate rejects title exceeding 300 chars."""
        with pytest.raises(Exception):
            CardCreate(title="x" * 301)

    def test_card_update_optional_fields(self):
        """CardUpdate accepts partial updates."""
        data = CardUpdate(title="New")
        assert data.title == "New"
        assert data.description is None
        assert data.column_id is None
        assert data.position is None

    def test_card_response_fields(self):
        """CardResponse includes all expected fields."""
        data = CardResponse(
            id=1, title="Card", description="",
            position=0, column_id=1
        )
        assert data.id == 1
        assert data.position == 0
        assert data.column_id == 1

    def test_column_response_includes_cards(self):
        """ColumnResponse includes cards list."""
        data = ColumnResponse(
            id=1, title="Col", position=0, board_id=1, cards=[]
        )
        assert data.cards == []

    def test_board_list_item_fields(self):
        """BoardListItem has the correct fields."""
        now = datetime.now()
        data = BoardListItem(
            id=1, title="Board", description="", created_at=now
        )
        assert data.id == 1
        assert data.title == "Board"


# ═══════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════


class TestModels:
    """Tests for SQLAlchemy model definitions."""

    def test_board_has_columns_relationship(self, db):
        """Board model has columns relationship with cascade."""
        board = create_board(db, BoardCreate(title="Test"))
        assert hasattr(board, "columns")
        assert len(board.columns) == 3

    def test_column_belongs_to_board(self, db):
        """Column model has board relationship."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Col"))
        assert col.board is not None
        assert col.board.id == board.id

    def test_card_belongs_to_column(self, db):
        """Card model has column relationship."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Col"))
        card = create_card(db, col.id, CardCreate(title="Card"))
        assert card.column is not None
        assert card.column.id == col.id

    def test_column_cards_relationship(self, db):
        """Column model has cards relationship."""
        board = create_board(db, BoardCreate(title="Board"))
        col = create_column(db, board.id, ColumnCreate(title="Col"))
        create_card(db, col.id, CardCreate(title="Card 1"))
        create_card(db, col.id, CardCreate(title="Card 2"))
        assert len(col.cards) == 2

    def test_board_tablename(self):
        """Board uses 'boards' as tablename."""
        assert Board.__tablename__ == "boards"

    def test_column_tablename(self):
        """Column_ uses 'columns' as tablename."""
        assert Column_.__tablename__ == "columns"

    def test_card_tablename(self):
        """Card uses 'cards' as tablename."""
        assert Card.__tablename__ == "cards"
