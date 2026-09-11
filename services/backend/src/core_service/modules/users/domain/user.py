"""User 도메인 엔티티 — schema.md §5 `users` 테이블 매핑. 외부 의존성 없음(순수 규칙만).

erd.md §1 "소유 루트(Ownership Root)" — 모든 엔티티는 직접/간접으로 users에 귀속된다.
"""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class PersonaSnapshot:
    """§2.11 4단계 "단기 압축 기억" — 여러 챕터의 Compaction 요약을 가로질러 압축한,
    말벗돌봄 모드(CareAgent "은빛이")가 다음 대화에서 참고할 배경지식. 정서·심리
    평가는 포함하지 않는다(decisions.md #25).

    `source_chapter_count`는 이 요약이 만들어질 때 참고한(=Compaction 요약이 있는)
    챕터 수 — 그 수가 바뀌면 stale로 간주한다(`Chapter.compaction_is_stale`과
    같은 목적의 더 단순한 버전 마커).
    """

    summary: str
    keywords: list[str]
    source_chapter_count: int


@dataclass
class User:
    id: UUID
    name: str
    birth_date: date | None
    primary_device_id: UUID | None
    created_at: datetime
    updated_at: datetime
    persona_snapshot: PersonaSnapshot | None = None

    def validate_name(self) -> None:
        """비즈니스 규칙: name은 schema.md상 NOT NULL, VARCHAR(100)."""
        if not self.name or len(self.name) > 100:
            raise ValueError("name은 1~100자여야 합니다.")

    def persona_is_stale(self, current_chapter_count: int) -> bool:
        """압축 대상 챕터 수가 마지막 생성 시점과 다르면(늘었거나 줄었으면) stale."""
        return (
            self.persona_snapshot is None
            or self.persona_snapshot.source_chapter_count != current_chapter_count
        )
