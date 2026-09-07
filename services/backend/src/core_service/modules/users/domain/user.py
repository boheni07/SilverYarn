"""User 도메인 엔티티 — schema.md §5 `users` 테이블 매핑. 외부 의존성 없음(순수 규칙만).

erd.md §1 "소유 루트(Ownership Root)" — 모든 엔티티는 직접/간접으로 users에 귀속된다.
"""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class User:
    id: UUID
    name: str
    birth_date: date | None
    primary_device_id: UUID | None
    created_at: datetime
    updated_at: datetime

    def validate_name(self) -> None:
        """비즈니스 규칙: name은 schema.md상 NOT NULL, VARCHAR(100)."""
        if not self.name or len(self.name) > 100:
            raise ValueError("name은 1~100자여야 합니다.")
