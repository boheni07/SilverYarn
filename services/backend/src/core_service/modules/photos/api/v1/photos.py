"""photos 리소스 라우터 — sync-contract.md §4 Presigned URL 흐름 구현.

⚠️ sync-contract.md §4의 예시 요청 본문(`{ "content_type", "file_size" }`)에는
`user_id`/`uploader_type`이 빠져 있다 — 이 사진이 누구 것인지 서버가 알아야 하는데
(photos.user_id NOT NULL) 문서 예시엔 없던 필드다. POST /devices, POST
/chapters/{id}/review 등 이 코드베이스의 지배적 패턴(소유자 ID를 요청 본문에 명시)을
따라 두 필드를 추가했다 — sync/upload처럼 Device Token → 기기 → 사용자로 신뢰
사슬을 타는 예외 패턴은 "가족이 웹콘솔에서 업로드"하는 경로에는 애초에 적용할 수
없어(디바이스가 없음) 선택하지 않았다.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.auth_deps import (
    AuthContext,
    ConsentDirectory,
    Principal,
    authorize_elder_data_read,
    authorize_user_access,
    get_consent_directory,
    require_auth,
    require_principal,
)
from core_service.core.clients.storage_client import StorageClient
from core_service.core.db import get_db
from core_service.modules.photo_requests.application.photo_request_service import PhotoRequestService
from core_service.modules.photo_requests.deps import get_photo_request_service
from core_service.modules.photos.application.photo_service import PhotoService
from core_service.modules.photos.domain.photo import UploaderType
from core_service.modules.photos.infrastructure.photo_repository import PhotoRepository
from core_service.shared.domain_enums import FamilyRole
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["photos"])


class PhotoUploadUrlRequest(BaseModel):
    user_id: uuid.UUID
    uploader_type: UploaderType
    content_type: str
    file_size: int


class PhotoUploadUrlResponse(BaseModel):
    photo_id: uuid.UUID
    upload_url: str
    expires_at: datetime


class PhotoCompleteResponse(BaseModel):
    photo_id: uuid.UUID
    status: str


class PhotoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    uploader_type: str
    status: str
    storage_ref: str
    caption: str | None
    year_tag: int | None
    recall_status: str
    placement_status: str
    inline_position: str | None
    linked_chunk_id: uuid.UUID | None
    linked_chapter_id: uuid.UUID | None
    quality_flag: str
    width: int | None
    height: int | None
    file_size_kb: int | None
    mime_type: str | None
    uploaded_at: datetime
    view_url: str | None


def _service(session: AsyncSession = Depends(get_db)) -> PhotoService:
    return PhotoService(PhotoRepository(session), StorageClient())


# design.md §7.1 — 사진 업로드는 family/caregiver/admin (또는 어르신 본인 기기).
_UPLOAD_ROLES = frozenset({FamilyRole.FAMILY, FamilyRole.CAREGIVER, FamilyRole.ADMIN})


@router.post("/photos/upload-url", response_model=DataResponse[PhotoUploadUrlResponse], status_code=200)
async def request_upload_url(
    body: PhotoUploadUrlRequest,
    service: PhotoService = Depends(_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[PhotoUploadUrlResponse]:
    """sync-contract.md §4 1단계 — MinIO Presigned PUT URL 발급, `photos` 행을
    status=pending_upload로 함께 생성한다."""
    authorize_user_access(principal, body.user_id, allowed_roles=_UPLOAD_ROLES)
    photo, upload_url, expires_at = await service.request_upload_url(
        user_id=body.user_id,
        uploader_type=body.uploader_type,
        content_type=body.content_type,
        file_size=body.file_size,
    )
    return DataResponse(
        data=PhotoUploadUrlResponse(photo_id=photo.id, upload_url=upload_url, expires_at=expires_at)
    )


@router.post("/photos/{photo_id}/complete", response_model=DataResponse[PhotoCompleteResponse])
async def complete_upload(
    photo_id: uuid.UUID,
    service: PhotoService = Depends(_service),
    photo_request_service: PhotoRequestService = Depends(get_photo_request_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[PhotoCompleteResponse]:
    """sync-contract.md §4 3단계 — 클라이언트가 MinIO에 직접 PUT을 마친 뒤 보내는
    확인 콜백. 멱등하다(이미 uploaded여도 성공).

    photo_requests 모듈을 deps.py로만 호출해 이 사용자의 대기 중인 사진 요청을
    전부 충족(fulfilled) 처리한다 — schema.md §3.7 `fulfilled_at`이 "사진 업로드로
    충족된 시각"이라고 이미 명시한 흐름이다. 어느 사진이 어느 요청에 대한 응답인지
    연결하는 FK가 없어 1:1 매핑은 못 하고, "이 사용자가 사진을 올렸다"를 대기 중인
    모든 요청에 대한 응답으로 해석한다(photo_request_service.py 참조).
    """
    photo = await service.complete_upload(photo_id)
    authorize_user_access(principal, photo.user_id, allowed_roles=_UPLOAD_ROLES)
    await photo_request_service.fulfill_pending_for_user(photo.user_id)
    return DataResponse(data=PhotoCompleteResponse(photo_id=photo.id, status=photo.status.value))


@router.get("/users/{user_id}/photos", response_model=DataResponse[list[PhotoResponse]])
async def list_user_photos(
    user_id: uuid.UUID,
    service: PhotoService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
    consent_directory: ConsentDirectory = Depends(get_consent_directory),
) -> DataResponse[list[PhotoResponse]]:
    """design.md §4.2 — 사진 목록 조회."""
    await authorize_elder_data_read(ctx, user_id, consent_directory)
    photos = await service.list_photos_for_user(user_id)
    return DataResponse(
        data=[
            PhotoResponse(
                id=p.id,
                user_id=p.user_id,
                uploader_type=p.uploader_type.value,
                status=p.status.value,
                storage_ref=p.storage_ref,
                caption=p.caption,
                year_tag=p.year_tag,
                recall_status=p.recall_status.value,
                placement_status=p.placement_status.value,
                inline_position=p.inline_position,
                linked_chunk_id=p.linked_chunk_id,
                linked_chapter_id=p.linked_chapter_id,
                quality_flag=p.quality_flag.value,
                width=p.width,
                height=p.height,
                file_size_kb=p.file_size_kb,
                mime_type=p.mime_type,
                uploaded_at=p.uploaded_at,
                view_url=service.get_view_url(p),
            )
            for p in photos
        ]
    )
