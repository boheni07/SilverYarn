"""User 유스케이스 — Presentation은 이 서비스만 호출하고 Repository를 직접 만지지 않는다."""

import uuid
from datetime import date
from typing import Protocol

from core_service.core.errors import ApiError
from core_service.modules.users.domain.user import User
from core_service.modules.users.infrastructure.user_repository import UserRepository


class PersonaSummarizer(Protocol):
    """design §2.11 4단계 — 챕터별 (요약, 키워드) 목록 → (전체 인물 요약, 키워드).
    `core.clients.LLMClient`가 구현."""

    async def summarize_persona_memory(
        self, chapter_digests: list[tuple[str, list[str]]]
    ) -> tuple[str, list[str]]: ...


class UserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ApiError("NOT_FOUND", f"사용자({user_id})를 찾을 수 없습니다.")
        return user

    async def create_user(self, name: str, birth_date: date | None) -> User:
        if not name or len(name) > 100:
            raise ApiError("VALIDATION_ERROR", "name은 1~100자여야 합니다.")
        return await self._repo.create(name=name, birth_date=birth_date)

    async def refresh_persona_snapshot(
        self,
        user_id: uuid.UUID,
        chapter_digests: list[tuple[str, list[str]]],
        summarizer: PersonaSummarizer,
        *,
        force: bool = False,
    ) -> User:
        """§2.11 4단계 "단기 압축 기억" 갱신 — `ChapterService.compact_chapter`와 동일한
        stale 판정 패턴(force가 아니면 참고 챕터 수가 그대로면 재호출 없이 그대로 반환).

        `chapter_digests`가 비어 있으면(아직 요약된 챕터가 하나도 없음) 요약할 게
        없으므로 vLLM을 부르지 않고 그대로 반환한다.
        """
        user = await self.get_user(user_id)
        current_count = len(chapter_digests)
        if not force and not user.persona_is_stale(current_count):
            return user
        if current_count == 0:
            return user
        summary, keywords = await summarizer.summarize_persona_memory(chapter_digests)
        await self._repo.set_persona_snapshot(
            user_id, summary=summary, keywords=keywords, source_chapter_count=current_count
        )
        return await self.get_user(user_id)

    async def list_users(self, page: int, page_size: int, name: str | None = None) -> tuple[list[User], int]:
        """apps/admin "전체 사용자 목록" — page는 1부터 시작(design.md §4.1 예시와 동일).
        name을 주면 부분일치 검색(ILIKE)으로 좁힌다."""
        if page < 1:
            raise ApiError("VALIDATION_ERROR", "page는 1 이상이어야 합니다.")
        if not (1 <= page_size <= 100):
            raise ApiError("VALIDATION_ERROR", "page_size는 1~100 사이여야 합니다.")
        offset = (page - 1) * page_size
        return await self._repo.list_all(offset=offset, limit=page_size, name=name)
