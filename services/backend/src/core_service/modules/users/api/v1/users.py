"""users 리소스 라우터 — design.md §4.1 표준 응답 포맷, snake_case wire format(decisions.md #20)."""

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import AuthContext, require_auth
from core_service.core.db import get_db
from core_service.modules.users.application.user_service import UserService
from core_service.modules.users.infrastructure.user_repository import UserRepository
from core_service.shared.schemas import DataResponse, PaginatedResponse, Pagination

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    name: str
    birth_date: date | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    birth_date: date | None
    primary_device_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


def _service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(session))


@router.post("", response_model=DataResponse[UserResponse], status_code=201)
async def create_user(
    body: UserCreateRequest,
    service: UserService = Depends(_service),
) -> DataResponse[UserResponse]:
    """온보딩 시 어르신(1차 사용자) 계정 생성."""
    user = await service.create_user(name=body.name, birth_date=body.birth_date)
    return DataResponse(data=UserResponse(**user.__dict__))


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    service: UserService = Depends(_service),
    # Admin — TODO: role 체크 강화 (devices.py list_user_devices와 동일 패턴).
    # apps/admin "전체 사용자 목록" 화면용(2026-09-08 신규) — design.md §4.1의
    # PaginatedResponse 봉투를 실제로 쓰는 첫 엔드포인트다.
    _ctx: AuthContext = Depends(require_auth),
) -> PaginatedResponse[UserResponse]:
    users, total = await service.list_users(page=page, page_size=page_size)
    return PaginatedResponse(
        data=[UserResponse(**u.__dict__) for u in users],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


@router.get("/{user_id}", response_model=DataResponse[UserResponse])
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(_service),
    _ctx: AuthContext = Depends(require_auth),
) -> DataResponse[UserResponse]:
    user = await service.get_user(user_id)
    return DataResponse(data=UserResponse(**user.__dict__))
