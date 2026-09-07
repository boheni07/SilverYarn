"""공통 응답 봉투 — design.md §4.1 표준 응답 포맷과 1:1 대응."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    data: T


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: Pagination
