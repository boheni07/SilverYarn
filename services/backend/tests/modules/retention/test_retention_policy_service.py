"""RetentionPolicyService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

decisions.md #56(Q5, 2026-09-13) — 보유기간을 DB 설정 테이블 + admin 콘솔로 조정.
"""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.retention.application.retention_policy_service import (
    RetentionPolicyService,
)
from core_service.modules.retention.domain.retention_policy import (
    RetentionCategory,
    RetentionPolicy,
)


class FakeRetentionPolicyRepository:
    def __init__(self) -> None:
        self._store: dict[str, RetentionPolicy] = {}

    async def get_by_category(self, category: str) -> RetentionPolicy | None:
        return self._store.get(category)

    async def list_all(self) -> list[RetentionPolicy]:
        return sorted(self._store.values(), key=lambda p: p.category)

    async def upsert(self, category: str, retention_days: int) -> RetentionPolicy:
        existing = self._store.get(category)
        policy = RetentionPolicy(
            id=existing.id if existing else uuid.uuid4(),
            category=category,
            retention_days=retention_days,
            updated_at=datetime.now(UTC),
        )
        self._store[category] = policy
        return policy


@pytest.fixture
def service() -> RetentionPolicyService:
    return RetentionPolicyService(FakeRetentionPolicyRepository())  # type: ignore[arg-type]


async def test_get_retention_days_falls_back_to_default_when_missing(
    service: RetentionPolicyService,
) -> None:
    days = await service.get_retention_days(RetentionCategory.CONVERSATION_TRANSCRIPT, default=365)
    assert days == 365


async def test_set_retention_days_then_get_returns_new_value(service: RetentionPolicyService) -> None:
    await service.set_retention_days(RetentionCategory.CONVERSATION_TRANSCRIPT, 30)
    days = await service.get_retention_days(RetentionCategory.CONVERSATION_TRANSCRIPT, default=365)
    assert days == 30


async def test_set_retention_days_rejects_zero(service: RetentionPolicyService) -> None:
    with pytest.raises(ApiError, match="1 이상"):
        await service.set_retention_days(RetentionCategory.CONVERSATION_TRANSCRIPT, 0)


async def test_set_retention_days_rejects_negative(service: RetentionPolicyService) -> None:
    with pytest.raises(ApiError, match="1 이상"):
        await service.set_retention_days(RetentionCategory.CONVERSATION_TRANSCRIPT, -5)


async def test_list_policies_returns_all_set_categories(service: RetentionPolicyService) -> None:
    await service.set_retention_days(RetentionCategory.CONVERSATION_TRANSCRIPT, 90)
    await service.set_retention_days("future_category", 10)
    policies = await service.list_policies()
    assert {p.category for p in policies} == {RetentionCategory.CONVERSATION_TRANSCRIPT, "future_category"}
