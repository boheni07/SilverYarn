"""Organization 도메인 엔티티 — schema.md §5 `organizations` 테이블 매핑.

decisions.md #59(2026-09-13, I2) — B2G 시설(요양원·복지관) 테넌시 **안전망**.
`users.org_id`/`family_members.org_id`가 이 엔티티를 가리킨다. 조직에 속한
어르신 전체를 자동으로 조회하는 권한 모델(B2G 대량 열람)은 이 라운드 범위 밖 —
기존 1:1 `family_members` 연결(admin 중개 초대, decisions #51)이 여전히 1차
권한 부여 경로이고, org_id는 "다른 시설 소속끼리는 그 연결이 있어도 차단"하는
2차 안전망으로만 쓰인다(`auth_deps.authorize_elder_data_read` 참조).
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Organization:
    id: UUID
    name: str
    created_at: datetime

    def validate_name(self) -> None:
        """비즈니스 규칙: name은 schema.md상 NOT NULL, VARCHAR(200)."""
        if not self.name or len(self.name) > 200:
            raise ValueError("name은 1~200자여야 합니다.")
