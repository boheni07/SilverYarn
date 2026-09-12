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
    # decisions.md #54(2026-09-12 사용자 결정, Q3) — 복지사(social_worker)의 어르신
    # 데이터 열람은 제17조 제3자제공으로 봐서 전용 동의가 필요하다(가족은 제26조
    # 위탁범위 내 이용이라 별도 동의 불필요). 이 동의가 있을 때만
    # `auth_deps.authorize_elder_data_read`가 social_worker의 열람을 허용한다.
    THIRD_PARTY_ACCESS = "third_party_access"
    # decisions.md #57(2026-09-12 사용자 결정, Q6) — FCM(구글, 미국 서버) 유지 결정에
    # 따라 푸시알림 발송 시 기기토큰이 국외로 이전된다. 개인정보보호법상 국외이전
    # 고지·동의 대상으로 보고, 온보딩에서 별도로(데이터수집 동의와 구분해) 받는다.
    # 알림 발송 채널(FCM 어댑터) 자체는 아직 미구현 — 이 동의는 그 구현에 앞서
    # 동의 이력을 먼저 확보해 두는 것(다른 여러 결정과 동일한 "코드보다 정책 먼저" 순서).
    INTERNATIONAL_TRANSFER = "international_transfer"


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
