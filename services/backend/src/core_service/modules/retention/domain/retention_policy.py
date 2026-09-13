"""RetentionPolicy 도메인 엔티티 — schema.md §5 `retention_policies` 테이블 매핑.

decisions.md #56(2026-09-13, Q5) — 보유기간을 하드코딩하지 않고 admin이 조정할
수 있는 설정으로 둔다. `category`는 지금은 `conversation_transcript` 하나뿐이지만
(원본음성은 이미 즉시삭제 #30, 챕터·사진은 계정 존속기간 동안 보관이라 만료
대상 아님) 스키마는 카테고리 추가를 전제로 일반화해 뒀다.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


class RetentionCategory:
    """알려진 카테고리 상수 — 도메인 enum이 아니라 문자열인 이유는 운영 중 새
    카테고리를 코드 배포 없이 SQL로 먼저 추가해볼 수 있게 하기 위해서다(YAGNI 반대
    방향 — 유연성이 필요한 지점으로 판단)."""

    CONVERSATION_TRANSCRIPT = "conversation_transcript"


@dataclass
class RetentionPolicy:
    id: UUID
    category: str
    retention_days: int
    updated_at: datetime

    def validate_retention_days(self) -> None:
        if self.retention_days < 1:
            raise ValueError("retention_days는 1 이상이어야 합니다.")
