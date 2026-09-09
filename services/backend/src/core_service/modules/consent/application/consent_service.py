"""ConsentLog 유스케이스 — design.md §2.9 온보딩 "개인정보 수집 동의" 단계의 서버측.

`current_state()`는 RBAC의 "동의 시" 조건(design.md §7.1 — social_worker 챕터 조회 등)과
외부 연계 게이트(§7 "미동의 시 전량 온프레미스 경로")가 쓸 수 있도록, 유형별 최신
행만 추려 현재 동의 상태를 돌려준다.
"""

import uuid

from core_service.modules.consent.domain.consent_log import ConsentLog, ConsentType
from core_service.modules.consent.infrastructure.consent_log_repository import ConsentLogRepository


class ConsentService:
    def __init__(self, repo: ConsentLogRepository):
        self._repo = repo

    async def record_consent(
        self,
        user_id: uuid.UUID,
        consent_type: ConsentType,
        granted: bool,
        granted_by: uuid.UUID | None,
    ) -> ConsentLog:
        return await self._repo.create(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_by=granted_by,
        )

    async def list_consent_logs(self, user_id: uuid.UUID) -> list[ConsentLog]:
        return await self._repo.list_by_user(user_id)

    async def current_state(self, user_id: uuid.UUID) -> dict[ConsentType, bool]:
        """유형별 최신 행 기준 현재 동의 상태. 한 번도 기록이 없는 유형은 키에서 빠진다
        (미동의와 동일하게 취급 — 호출자가 `.get(type, False)`로 읽으면 된다)."""
        logs = await self._repo.list_by_user(user_id)  # granted_at DESC
        state: dict[ConsentType, bool] = {}
        for log in logs:
            state.setdefault(log.consent_type, log.granted)
        return state
