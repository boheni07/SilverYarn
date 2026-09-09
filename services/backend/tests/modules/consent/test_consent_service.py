"""ConsentService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: design.md §2.9 온보딩 동의 기록, actor 파생(CTO B2), current_state()가
유형별 최신 행만 반영하는지(동의→철회→재동의 시나리오).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from core_service.modules.consent.application.consent_service import ConsentService
from core_service.modules.consent.domain.consent_log import ConsentActor, ConsentLog, ConsentType


class FakeConsentLogRepository:
    def __init__(self) -> None:
        self._store: list[ConsentLog] = []
        self._clock = datetime(2026, 1, 1, tzinfo=UTC)

    async def list_by_user(self, user_id: uuid.UUID) -> list[ConsentLog]:
        rows = [log for log in self._store if log.user_id == user_id]
        return sorted(rows, key=lambda log: log.granted_at, reverse=True)

    async def create(
        self,
        user_id: uuid.UUID,
        consent_type: ConsentType,
        granted: bool,
        granted_by: uuid.UUID | None,
    ) -> ConsentLog:
        self._clock += timedelta(seconds=1)  # 생성 순서를 granted_at으로 구분
        log = ConsentLog(
            id=uuid.uuid4(),
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_by=granted_by,
            granted_at=self._clock,
        )
        self._store.append(log)
        return log


@pytest.fixture
def repo() -> FakeConsentLogRepository:
    return FakeConsentLogRepository()


@pytest.fixture
def service(repo: FakeConsentLogRepository) -> ConsentService:
    return ConsentService(repo)  # type: ignore[arg-type]


async def test_self_consent_has_no_granted_by(service: ConsentService) -> None:
    user_id = uuid.uuid4()
    log = await service.record_consent(user_id, ConsentType.DATA_COLLECTION, granted=True, granted_by=None)
    assert log.granted is True
    assert log.granted_by is None
    assert log.actor == ConsentActor.SELF


async def test_proxy_consent_records_family_member(service: ConsentService) -> None:
    user_id = uuid.uuid4()
    family_id = uuid.uuid4()
    log = await service.record_consent(
        user_id, ConsentType.DATA_COLLECTION, granted=True, granted_by=family_id
    )
    assert log.granted_by == family_id
    assert log.actor == ConsentActor.PROXY


async def test_current_state_reflects_latest_row_per_type(service: ConsentService) -> None:
    user_id = uuid.uuid4()
    await service.record_consent(user_id, ConsentType.DATA_COLLECTION, granted=True, granted_by=None)
    await service.record_consent(user_id, ConsentType.EXTERNAL_TTS_OPTIN, granted=True, granted_by=None)
    # data_collection 철회
    await service.record_consent(user_id, ConsentType.DATA_COLLECTION, granted=False, granted_by=None)

    state = await service.current_state(user_id)
    assert state[ConsentType.DATA_COLLECTION] is False
    assert state[ConsentType.EXTERNAL_TTS_OPTIN] is True
    assert ConsentType.EXTERNAL_LLM_OPTIN not in state  # 기록 없음 → 키 없음


async def test_current_state_empty_when_no_logs(service: ConsentService) -> None:
    assert await service.current_state(uuid.uuid4()) == {}


async def test_list_returns_newest_first(service: ConsentService) -> None:
    user_id = uuid.uuid4()
    await service.record_consent(user_id, ConsentType.DATA_COLLECTION, granted=True, granted_by=None)
    await service.record_consent(user_id, ConsentType.DATA_COLLECTION, granted=False, granted_by=None)

    logs = await service.list_consent_logs(user_id)
    assert [log.granted for log in logs] == [False, True]


async def test_list_scoped_to_user(service: ConsentService) -> None:
    user_a, user_b = uuid.uuid4(), uuid.uuid4()
    await service.record_consent(user_a, ConsentType.DATA_COLLECTION, granted=True, granted_by=None)
    await service.record_consent(user_b, ConsentType.DATA_COLLECTION, granted=True, granted_by=None)

    assert len(await service.list_consent_logs(user_a)) == 1
