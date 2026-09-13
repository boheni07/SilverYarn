"""users 리소스 라우터 — design.md §4.1 표준 응답 포맷, snake_case wire format(decisions.md #20)."""

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.auth_deps import AuthContext, authorize_user_access, require_auth, require_roles
from core_service.core.clients.graph_client import GraphClient
from core_service.core.clients.storage_client import StorageClient
from core_service.core.clients.vectordb_client import VectorDBClient
from core_service.core.db import get_db
from core_service.core.deletion_log import DeletionRecordRepository
from core_service.modules.organizations.application.organization_service import (
    OrganizationService,
)
from core_service.modules.organizations.deps import get_organization_service
from core_service.modules.photos.infrastructure.photo_repository import PhotoRepository
from core_service.modules.users.application.user_erasure_service import UserErasureService
from core_service.modules.users.application.user_service import UserService
from core_service.modules.users.infrastructure.user_repository import UserRepository
from core_service.shared.domain_enums import FamilyRole
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
    org_id: uuid.UUID | None = None


class UserOrganizationRequest(BaseModel):
    org_id: uuid.UUID | None


class UserEraseRequest(BaseModel):
    # decisions.md #56(Q5) — 정보주체 삭제요청권(PIPA) 행사 사유 기록용. 실수 클릭
    # 방지를 위해 사유를 필수로 받는다(빈 문자열은 UserErasureService가 막지 않지만
    # admin UI에서 확인 문구 입력을 강제한다).
    reason: str
    # 실행을 요청한 구성원(가족/관리자) — photo_requests와 동일한 패턴
    # (auth_deps.AuthContext에는 family_member_id가 없어 본인 것을 명시적으로 넘긴다).
    # None이면 익명 관리자 작업으로 기록된다.
    requested_by: uuid.UUID | None = None


def _service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(session))


def _erasure_service(session: AsyncSession = Depends(get_db)) -> UserErasureService:
    return UserErasureService(
        UserRepository(session),
        PhotoRepository(session),
        DeletionRecordRepository(session),
        VectorDBClient(),
        GraphClient(),
        StorageClient(),
    )


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
    name: str | None = None,
    service: UserService = Depends(_service),
    # apps/admin "전체 사용자 목록" 화면용 — design.md §7.1 "사용자 관리 = admin 전용".
    # name은 이름 검색 필터(ILIKE 부분일치).
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> PaginatedResponse[UserResponse]:
    users, total = await service.list_users(page=page, page_size=page_size, name=name)
    return PaginatedResponse(
        data=[UserResponse(**u.__dict__) for u in users],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


@router.get("/{user_id}", response_model=DataResponse[UserResponse])
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[UserResponse]:
    authorize_user_access(ctx, user_id)
    user = await service.get_user(user_id)
    return DataResponse(data=UserResponse(**user.__dict__))


@router.put("/{user_id}/organization", response_model=DataResponse[UserResponse])
async def set_user_organization(
    user_id: uuid.UUID,
    body: UserOrganizationRequest,
    service: UserService = Depends(_service),
    org_service: OrganizationService = Depends(get_organization_service),
    # decisions.md #59(I2) — 어르신을 B2G 시설에 소속시키는 건 admin(B2G 운영) 전용.
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> DataResponse[UserResponse]:
    """apps/admin "시설 관리" — 어르신을 시설에 배정(`org_id` 지정)하거나 해제(null)."""
    if body.org_id is not None:
        await org_service.ensure_exists(body.org_id)  # 없으면 VALIDATION_ERROR
    user = await service.set_organization(user_id, body.org_id)
    return DataResponse(data=UserResponse(**user.__dict__))


@router.post("/{user_id}/erase", status_code=204)
async def erase_user(
    user_id: uuid.UUID,
    body: UserEraseRequest,
    service: UserErasureService = Depends(_erasure_service),
    # decisions.md #56(Q5) — 계정 전체 삭제(crypto-shredding + 5개 저장소 정리)는
    # 되돌릴 수 없다. admin 전용으로 제한(§4.1 "관리자 콘솔 전용" 패턴, organization
    # 배정 엔드포인트와 동일 근거).
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> None:
    """어르신 계정 전체 삭제(erasure) — Postgres cascade + Qdrant/Neo4j/MinIO 정리 +
    `deletion_records` 감사 로그."""
    await service.erase_user(user_id, requested_by=body.requested_by, reason=body.reason)
