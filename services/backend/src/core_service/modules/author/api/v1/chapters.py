"""chapters 리소스 라우터 — design.md §4.2 목록에 있는 2건(list/review)에 더해,
그 목록을 실제로 쓰려면 필요한 단건 조회 2건(chapter, revisions)을 스캐폴딩 시점에
합리적 추가로 넣었다(design.md §4.2에는 없음 — 표에 반영 필요 여부는 다음 문서
동기화 라운드에서 검토).
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import AuthContext, require_auth
from core_service.core.db import get_db
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.domain.chapter import RevisionAction
from core_service.modules.author.infrastructure.chapter_repository import ChapterRepository
from core_service.modules.author.infrastructure.chapter_revision_repository import (
    ChapterRevisionRepository,
)
from core_service.modules.family_members.application.family_member_service import (
    FamilyMemberService,
)
from core_service.modules.family_members.deps import get_family_member_service
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["chapters"])


class ChapterResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    chapter_no: int
    title: str
    period: str
    body_text: str
    status: str
    version: int
    updated_at: datetime


class ChapterRevisionResponse(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    version: int
    body_text_snapshot: str
    reviewer_id: uuid.UUID | None
    review_comment: str | None
    action: str
    created_at: datetime


class ChapterReviewRequest(BaseModel):
    action: RevisionAction
    review_comment: str | None = None
    # TODO(Keycloak 연동 후 제거): 지금은 AuthContext가 스텁이라 "현재 로그인한
    # 가족 구성원"을 토큰에서 구할 수 없어, 호출자가 reviewer_id를 직접 넘긴다.
    # family_members 모듈에 실존하는 id인지는 아래 review_chapter()에서 검증한다.
    reviewer_id: uuid.UUID | None = None


def _service(session: AsyncSession = Depends(get_db)) -> ChapterService:
    return ChapterService(ChapterRepository(session), ChapterRevisionRepository(session))


def _to_response(chapter) -> ChapterResponse:  # noqa: ANN001 — Chapter 도메인 dataclass
    return ChapterResponse(
        id=chapter.id,
        user_id=chapter.user_id,
        chapter_no=chapter.chapter_no,
        title=chapter.title,
        period=chapter.period.value,
        body_text=chapter.body_text,
        status=chapter.status.value,
        version=chapter.version,
        updated_at=chapter.updated_at,
    )


@router.get("/users/{user_id}/chapters", response_model=DataResponse[list[ChapterResponse]])
async def list_user_chapters(
    user_id: uuid.UUID,
    service: ChapterService = Depends(_service),
    _ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[ChapterResponse]]:
    """design.md §4.2 — 챕터 목록/본문 조회."""
    chapters = await service.list_chapters_for_user(user_id)
    return DataResponse(data=[_to_response(c) for c in chapters])


@router.get("/chapters/{chapter_id}", response_model=DataResponse[ChapterResponse])
async def get_chapter(
    chapter_id: uuid.UUID,
    service: ChapterService = Depends(_service),
    _ctx: AuthContext = Depends(require_auth),
) -> DataResponse[ChapterResponse]:
    chapter = await service.get_chapter(chapter_id)
    return DataResponse(data=_to_response(chapter))


@router.get("/chapters/{chapter_id}/revisions", response_model=DataResponse[list[ChapterRevisionResponse]])
async def list_chapter_revisions(
    chapter_id: uuid.UUID,
    service: ChapterService = Depends(_service),
    _ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[ChapterRevisionResponse]]:
    revisions = await service.list_revisions(chapter_id)
    return DataResponse(
        data=[
            ChapterRevisionResponse(
                id=r.id,
                chapter_id=r.chapter_id,
                version=r.version,
                body_text_snapshot=r.body_text_snapshot,
                reviewer_id=r.reviewer_id,
                review_comment=r.review_comment,
                action=r.action.value,
                created_at=r.created_at,
            )
            for r in revisions
        ]
    )


@router.post("/chapters/{chapter_id}/review", response_model=DataResponse[ChapterResponse])
async def review_chapter(
    chapter_id: uuid.UUID,
    body: ChapterReviewRequest,
    service: ChapterService = Depends(_service),
    family_service: FamilyMemberService = Depends(get_family_member_service),
    ctx: AuthContext = Depends(require_auth),  # TODO: role(family)만 허용하도록 강화
) -> DataResponse[ChapterResponse]:
    """design.md §4.2 — 감수 승인/반려 (chapter_revisions 생성은 이 시점에만 발생, M-5).

    reviewer_id가 넘어오면 family_members 모듈에 실존하는지 먼저 검증한다(잘못된
    id로 서명 기록이 남는 것을 막기 위함) — 없으면 FamilyMemberService.get_family_member가
    NOT_FOUND를 던진다. AuthContext(ctx)에서 자동으로 구하지 못하는 이유는 위 요청 필드
    주석 참조 — Keycloak 연동 후에는 이 파라미터 없이 ctx에서 바로 구하도록 바꾼다.
    """
    _ = ctx
    if body.reviewer_id is not None:
        await family_service.get_family_member(body.reviewer_id)  # 존재하지 않으면 NOT_FOUND
    chapter = await service.review_chapter(
        chapter_id=chapter_id,
        reviewer_id=body.reviewer_id,
        action=body.action,
        comment=body.review_comment,
    )
    return DataResponse(data=_to_response(chapter))
