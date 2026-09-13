"""Publication 유스케이스 — design.md §2.6 출판/인쇄 파이프라인의 접수·조회.

`SyncService`(sync 모듈)와 동일한 분리 원칙: 이 서비스는 "출판 요청 접수"(검증 +
`requested` 행 생성 + arq 잡 enqueue)와 조회만 담당하고, 실제 조판(PDF/ePub 생성)은
`worker.py` + `BookBuilderService`가 맡는다.
"""

import uuid

from arq.connections import ArqRedis

from core_service.core.errors import ApiError
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.domain.chapter import ChapterStatus
from core_service.modules.publications.domain.publication import Publication, PublicationFormat
from core_service.modules.publications.infrastructure.publication_repository import (
    PublicationRepository,
)


class PublicationService:
    def __init__(self, repo: PublicationRepository, chapter_service: ChapterService, arq_pool: ArqRedis):
        self._repo = repo
        self._chapters = chapter_service
        self._pool = arq_pool

    async def request_publication(self, user_id: uuid.UUID, fmt: PublicationFormat) -> Publication:
        """design.md §2.6 "전체 챕터 confirmed 상태 도달 → 출판 요청" 전제조건을 검증한다.
        챕터가 하나도 없거나 하나라도 `confirmed`가 아니면 아직 출판할 자서전이
        완성되지 않은 것이므로 요청 자체를 막는다(하드코딩된 특정 챕터 수 조건이
        아니라 "전부 확정"이라는 상태 조건)."""
        chapters = await self._chapters.list_chapters_for_user(user_id)
        if not chapters:
            raise ApiError("VALIDATION_ERROR", "출판할 챕터가 아직 없습니다.")
        not_confirmed = [c for c in chapters if c.status != ChapterStatus.CONFIRMED]
        if not_confirmed:
            raise ApiError(
                "VALIDATION_ERROR",
                f"아직 확정되지 않은 챕터가 {len(not_confirmed)}건 있습니다. "
                "모든 챕터가 확정(가족 감수 완료) 상태여야 출판을 요청할 수 있습니다.",
            )

        publication = await self._repo.create(user_id, fmt)
        await self._pool.enqueue_job("process_publication", publication_id=str(publication.id))
        return publication

    async def get_publication(self, publication_id: uuid.UUID) -> Publication:
        publication = await self._repo.get_by_id(publication_id)
        if publication is None:
            raise ApiError("NOT_FOUND", f"출판 요청({publication_id})을 찾을 수 없습니다.")
        return publication

    async def list_publications_for_user(self, user_id: uuid.UUID) -> list[Publication]:
        return await self._repo.list_by_user(user_id)
