"""RetentionPolicy 유스케이스 — decisions.md #56(Q5)."""

from core_service.core.errors import ApiError
from core_service.modules.retention.domain.retention_policy import RetentionPolicy
from core_service.modules.retention.infrastructure.retention_policy_repository import (
    RetentionPolicyRepository,
)


class RetentionPolicyService:
    def __init__(self, repo: RetentionPolicyRepository):
        self._repo = repo

    async def list_policies(self) -> list[RetentionPolicy]:
        return await self._repo.list_all()

    async def get_retention_days(self, category: str, *, default: int) -> int:
        """정책 행이 아직 없으면(신규 카테고리, 마이그레이션 미반영 등) `default`로
        안전하게 폴백한다 — 보유기간 계산이 정책 조회 실패로 막히면 안 된다."""
        policy = await self._repo.get_by_category(category)
        return policy.retention_days if policy else default

    async def set_retention_days(self, category: str, retention_days: int) -> RetentionPolicy:
        if retention_days < 1:
            raise ApiError("VALIDATION_ERROR", "retention_days는 1 이상이어야 합니다.")
        return await self._repo.upsert(category, retention_days)
