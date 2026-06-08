"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Card Schemas ──

class CardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    column_id: Optional[int] = None
    position: Optional[int] = None


class CardResponse(CardBase):
    id: int
    position: int
    column_id: int

    model_config = {"from_attributes": True}


# ── Column Schemas ──

class ColumnBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class ColumnCreate(ColumnBase):
    position: int = 0


class ColumnUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    position: Optional[int] = None


class ColumnResponse(ColumnBase):
    id: int
    position: int
    board_id: int
    cards: list[CardResponse] = []

    model_config = {"from_attributes": True}


# ── Board Schemas ──

class BoardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""


class BoardCreate(BoardBase):
    pass


class BoardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class BoardResponse(BoardBase):
    id: int
    created_at: datetime
    updated_at: datetime
    columns: list[ColumnResponse] = []

    model_config = {"from_attributes": True}


class BoardListItem(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}
