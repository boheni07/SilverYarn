"""Chapter 유스케이스 — workflow-diagrams.md §4(작가 엔진)·§7(가족 협업·감수) 매핑.

§4(초안 생성/갱신)와 §7(감수)은 서로 다른 유스케이스로 분리돼 있다:
  - save_draft(): 작가 엔진(향후 worker.py 파이프라인)이 호출 — chapter_revisions 미생성
  - review_chapter(): 가족 웹 콘솔이 호출(API 경유) — 이때만 chapter_revisions 생성
이 분리는 3차 검증 M-5에서 정정된 워크플로우 오류(감수 전 이력 생성)를 코드 레벨에서
다시 어기지 않기 위한 것이다.
"""

import uuid
from datetime import datetime
from typing import Protocol

from core_service.core.errors import ApiError
from core_service.modules.author.domain.chapter import (
    Chapter,
    ChapterPeriod,
    ChapterRevision,
    ChapterStatus,
    RevisionAction,
)
from core_service.modules.author.infrastructure.chapter_repository import ChapterRepository
from core_service.modules.author.infrastructure.chapter_revision_repository import (
    ChapterRevisionRepository,
)


class ChapterCompactor(Protocol):
    """design §2.11 4단계 — 확정 챕터 본문 → (요약, 키워드). `core.clients.LLMClient`가 구현."""

    async def compact_chapter(self, body_text: str) -> tuple[str, list[str]]: ...


class ChapterService:
    def __init__(self, chapters: ChapterRepository, revisions: ChapterRevisionRepository):
        self._chapters = chapters
        self._revisions = revisions

    async def get_chapter(self, chapter_id: uuid.UUID) -> Chapter:
        chapter = await self._chapters.get_by_id(chapter_id)
        if chapter is None:
            raise ApiError("NOT_FOUND", f"챕터({chapter_id})를 찾을 수 없습니다.")
        return chapter

    async def list_chapters_for_user(self, user_id: uuid.UUID) -> list[Chapter]:
        return await self._chapters.list_by_user(user_id)

    async def list_chapter_updates_for_user(
        self, user_id: uuid.UUID, since: datetime | None = None
    ) -> list[Chapter]:
        """GET /sync/download가 쓰는 증분 조회 — sync-contract.md §5."""
        return await self._chapters.list_updated_since(user_id, since)

    async def get_chapter_by_user_and_no(self, user_id: uuid.UUID, chapter_no: int) -> Chapter | None:
        """UploadPipelineService가 기존 챕터 본문(있으면)을 조회할 때 사용 —
        모듈 경계 규칙상 다른 모듈이 ChapterRepository를 직접 만지지 않도록
        이 공개 메서드를 통해서만 조회하게 한다."""
        return await self._chapters.get_by_user_and_no(user_id, chapter_no)

    async def save_draft(
        self,
        user_id: uuid.UUID,
        chapter_no: int,
        title: str,
        period: ChapterPeriod,
        body_text: str,
    ) -> Chapter:
        """workflow-diagrams.md §4 O2단계 — chapters(draft/in_review) 저장. TODO: worker.py에서 호출."""
        if not title or len(title) > 200:
            raise ApiError("VALIDATION_ERROR", "title은 1~200자여야 합니다.")
        if not body_text:
            raise ApiError("VALIDATION_ERROR", "body_text는 비어 있을 수 없습니다.")
        return await self._chapters.upsert_draft(
            user_id=user_id, chapter_no=chapter_no, title=title, period=period, body_text=body_text
        )

    async def compact_chapter(
        self, chapter_id: uuid.UUID, compactor: ChapterCompactor, *, force: bool = False
    ) -> Chapter:
        """design §2.11 4단계 — 챕터 본문을 온디바이스 FTS5용 요약·키워드로 압축·저장.

        요약이 이미 현재 본문 버전에 대해 최신이면(`force`가 아니면) LLM을 호출하지
        않고 그대로 돌려준다 — 파이프라인이 턴마다 호출해도 중복 작업이 없다.
        """
        chapter = await self.get_chapter(chapter_id)
        if not force and not chapter.compaction_is_stale:
            return chapter
        summary, keywords = await compactor.compact_chapter(chapter.body_text)
        await self._chapters.set_compaction(
            chapter.id, summary=summary, keywords=keywords, source_version=chapter.version
        )
        return await self.get_chapter(chapter_id)

    async def list_revisions(self, chapter_id: uuid.UUID) -> list[ChapterRevision]:
        await self.get_chapter(chapter_id)  # 존재 확인
        return await self._revisions.list_by_chapter(chapter_id)

    async def review_chapter(
        self,
        chapter_id: uuid.UUID,
        reviewer_id: uuid.UUID | None,
        action: RevisionAction,
        comment: str | None,
    ) -> Chapter:
        """workflow-diagrams.md §7 — 승인/반려. 이 메서드만이 chapter_revisions를 생성한다."""
        chapter = await self.get_chapter(chapter_id)
        try:
            chapter.ensure_reviewable()
        except ValueError as exc:
            raise ApiError("CONFLICT", str(exc)) from exc

        await self._revisions.create(
            chapter_id=chapter.id,
            user_id=chapter.user_id,  # body_text_snapshot 암호화용 DEK 소유자
            version=chapter.version,
            body_text_snapshot=chapter.body_text,
            reviewer_id=reviewer_id,
            review_comment=comment,
            action=action,
        )

        new_status = ChapterStatus.CONFIRMED if action == RevisionAction.APPROVED else ChapterStatus.REJECTED
        return await self._chapters.update_status(chapter.id, new_status)
