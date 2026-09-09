"""ConsentLog 도메인 엔티티 — schema.md §3.14 `consent_logs` 테이블 매핑.

design.md §2.9 온보딩 흐름의 "개인정보 수집 동의" 단계가 남기는 이력. 각 동의/철회가
새 행이며(불변 로그) 최신 행이 현재 상태다.

**actor 개념 (CTO 검토 B2 대응, 스키마 변경 없음)**: `granted_by`가 없으면 어르신 본인
동의(`self`), 있으면 가족 대리 동의(`proxy`)로 해석한다. CTO B2가 권고한 명시적
enum(self/proxy/**legal_guardian**)과 `data_subject` RBAC 행 신설은 성년후견 대리동의의
법적 근거가 법무 검토(decisions.md #12 관련) 대기 중이라 이번 라운드에서는 도입하지
않는다 — `legal_guardian`을 코드가 임의로 정의하면 안 되기 때문.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConsentType(StrEnum):
    DATA_COLLECTION = "data_collection"
    EXTERNAL_TTS_OPTIN = "external_tts_optin"
    EXTERNAL_LLM_OPTIN = "external_llm_optin"


class ConsentActor(StrEnum):
    """동의를 실제로 수행한 주체 — 저장 컬럼이 아니라 `granted_by` 유무로 파생한다."""

    SELF = "self"
    PROXY = "proxy"


@dataclass
class ConsentLog:
    id: UUID
    user_id: UUID
    consent_type: ConsentType
    granted: bool
    granted_by: UUID | None
    granted_at: datetime

    @property
    def actor(self) -> ConsentActor:
        return ConsentActor.PROXY if self.granted_by is not None else ConsentActor.SELF
