"""publications 리소스 라우터 — design.md §4.2, §2.6 출판/인쇄 파이프라인."""

import uuid
from datetime import datetime, timedelta

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.auth_deps import (
    WRITE_ELDER_DATA_ROLES,
    AuthContext,
    Principal,
    authorize_user_access,
    require_auth,
    require_principal,
)
from core_service.core.clients.storage_client import StorageClient
from core_service.core.db import get_db
from core_service.core.queue import get_arq_pool
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.deps import get_chapter_service
from core_service.modules.publications.application.publication_service import PublicationService
from core_service.modules.publications.domain.publication import Publication, PublicationFormat
from core_service.modules.publications.infrastructure.publication_repository import (
    PublicationRepository,
)
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["publications"])


class PublicationRequestBody(BaseModel):
    format: PublicationFormat


class PublicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    format: str
    status: str
    requested_at: datetime
    completed_at: datetime | None
    download_url: str | None = None


def _service(
    session: AsyncSession = Depends(get_db),
    chapter_service: ChapterService = Depends(get_chapter_service),
    pool: ArqRedis = Depends(get_arq_pool),
) -> PublicationService:
    return PublicationService(PublicationRepository(session), chapter_service, pool)


def _to_response(publication: Publication, storage: StorageClient) -> PublicationResponse:
    download_url = None
    if publication.storage_ref is not None:
        # ready/delivered 상태에서만 storage_ref가 채워진다 — 완성본은 presigned GET URL로만
        # 노출한다(사진과 동일 원칙, 버킷을 public-read로 열지 않음).
        download_url = storage.presigned_get_url(
            publication.storage_ref, expires=timedelta(minutes=15), bucket=storage.publications_bucket
        )
    return PublicationResponse(
        id=publication.id,
        user_id=publication.user_id,
        format=publication.format.value,
        status=publication.status.value,
        requested_at=publication.requested_at,
        completed_at=publication.completed_at,
        download_url=download_url,
    )


@router.post(
    "/users/{user_id}/publications", response_model=DataResponse[PublicationResponse], status_code=201
)
async def request_publication(
    user_id: uuid.UUID,
    body: PublicationRequestBody,
    service: PublicationService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[PublicationResponse]:
    """design.md §4.2/§2.6 — 인쇄/출판 요청. 전체 챕터가 confirmed여야 접수된다."""
    authorize_user_access(ctx, user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    publication = await service.request_publication(user_id, body.format)
    return DataResponse(data=_to_response(publication, StorageClient()))


@router.get("/users/{user_id}/publications", response_model=DataResponse[list[PublicationResponse]])
async def list_user_publications(
    user_id: uuid.UUID,
    service: PublicationService = Depends(_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[list[PublicationResponse]]:
    authorize_user_access(principal, user_id)
    publications = await service.list_publications_for_user(user_id)
    storage = StorageClient()
    return DataResponse(data=[_to_response(p, storage) for p in publications])


@router.get("/publications/{publication_id}", response_model=DataResponse[PublicationResponse])
async def get_publication(
    publication_id: uuid.UUID,
    service: PublicationService = Depends(_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[PublicationResponse]:
    """출판 요청 단건 조회 — 상태 폴링 + 완성 시 download_url 확인용(신규,
    photo_requests/invitations와 동일 이유로 스캐폴딩 시점에 함께 추가)."""
    publication = await service.get_publication(publication_id)
    authorize_user_access(principal, publication.user_id)
    return DataResponse(data=_to_response(publication, StorageClient()))
