"""CRUD operations for the Kanban Board."""
from sqlalchemy.orm import Session

from app.models import Board, Column_, Card
from app.schemas import (
    BoardCreate, BoardUpdate,
    ColumnCreate, ColumnUpdate,
    CardCreate, CardUpdate,
)


# ── Board CRUD ──

def list_boards(db: Session) -> list[Board]:
    return db.query(Board).order_by(Board.updated_at.desc()).all()


def get_board(db: Session, board_id: int) -> Board | None:
    return db.query(Board).filter(Board.id == board_id).first()


def create_board(db: Session, data: BoardCreate) -> Board:
    board = Board(title=data.title, description=data.description)
    db.add(board)
    db.flush()
    for i, col_title in enumerate(["To Do", "In Progress", "Done"]):
        col = Column_(title=col_title, position=i, board_id=board.id)
        db.add(col)
    db.commit()
    db.refresh(board)
    return board


def update_board(db: Session, board_id: int, data: BoardUpdate) -> Board | None:
    board = get_board(db, board_id)
    if not board:
        return None
    if data.title is not None:
        board.title = data.title
    if data.description is not None:
        board.description = data.description
    db.commit()
    db.refresh(board)
    return board


def delete_board(db: Session, board_id: int) -> bool:
    board = get_board(db, board_id)
    if not board:
        return False
    db.delete(board)
    db.commit()
    return True


# ── Column CRUD ──

def create_column(db: Session, board_id: int, data: ColumnCreate) -> Column_ | None:
    board = get_board(db, board_id)
    if not board:
        return None
    col = Column_(title=data.title, position=data.position, board_id=board_id)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


def update_column(db: Session, column_id: int, data: ColumnUpdate) -> Column_ | None:
    col = db.query(Column_).filter(Column_.id == column_id).first()
    if not col:
        return None
    if data.title is not None:
        col.title = data.title
    if data.position is not None:
        col.position = data.position
    db.commit()
    db.refresh(col)
    return col


def delete_column(db: Session, column_id: int) -> bool:
    col = db.query(Column_).filter(Column_.id == column_id).first()
    if not col:
        return False
    db.delete(col)
    db.commit()
    return True


# ── Card CRUD ──

def create_card(db: Session, column_id: int, data: CardCreate) -> Card | None:
    col = db.query(Column_).filter(Column_.id == column_id).first()
    if not col:
        return None
    
    max_pos = db.query(Card.position).filter(Card.column_id == column_id).order_by(Card.position.desc()).first()
    position = (max_pos[0] + 1) if max_pos else 0
    card = Card(title=data.title, description=data.description, position=position, column_id=column_id)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def update_card(db: Session, card_id: int, data: CardUpdate) -> Card | None:
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        return None
    if data.title is not None:
        card.title = data.title
    if data.description is not None:
        card.description = data.description
    if data.column_id is not None:
        card.column_id = data.column_id
    if data.position is not None:
        card.position = data.position
    db.commit()
    db.refresh(card)
    return card


def delete_card(db: Session, card_id: int) -> bool:
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        return False
    db.delete(card)
    db.commit()
    return True
