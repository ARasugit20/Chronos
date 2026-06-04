from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    next_cursor: UUID | None
    has_more: bool
    limit: int


class CursorPage(BaseModel, Generic[T]):
    data: list[T]
    next_cursor: UUID | None
    has_more: bool
