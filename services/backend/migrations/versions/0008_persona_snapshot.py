"""사용자 단기 압축 기억(Short-term Compressed Persona) JSON 룰셋

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-11

SoR: docs/02-design/features/silveryarn-platform.design.md §2.11(4단계 Compaction
Engine — "다음 대화용 단기 압축 기억 JSON 룰셋 생성" §2.10 페르소나 정의와 연동),
schema.md §5.

## 무엇을 바꾸나
챕터별 Compaction(요약·키워드, 마이그레이션 0007)이 "이 챕터가 무슨 내용인가"라면,
이건 "이 어르신이 누구인가"를 여러 챕터에 걸쳐 압축한 것 — 말벗돌봄 모드(M4,
CareAgent "은빛이")가 다음 대화를 시작할 때 참고할 짧은 배경지식이다.
`users`에 3개 컬럼을 추가한다:

- `persona_summary`              VARCHAR(500) NULL — vLLM이 만든 2문장 이내 요약
- `persona_keywords`             TEXT[]        NULL — 핵심 키워드 5~8개
- `persona_source_chapter_count` INTEGER       NULL — 생성 시점에 참고한(=Compaction
    요약이 있는) 챕터 수. 그 수가 바뀌면(새 챕터가 요약됨) stale로 보고 재계산한다 —
    `chapters.compacted_version`과 같은 목적의 더 단순한 버전 마커.

⚠️ 정서 상태·심리 평가는 절대 포함하지 않는다(decisions.md #25 — 정서 모니터링
파이프라인은 법무 회신 전까지 피처플래그 OFF). 이 필드는 사실·인물·시대·장소 등
비-정서적 배경지식만 담는다 — `core/clients/llm_client.py`의 프롬프트가 이를 명시적으로
지시한다.

`compaction_summary`(마이그레이션 0007)와 동일하게 평문 저장이다 — 파생 요약 컬럼은
원본(`chapters.body_text`)만큼 민감하지 않다고 이미 판단한 전례를 따른다(일관성
우선, 재검토는 별도 이슈).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    "ALTER TABLE users ADD COLUMN persona_summary VARCHAR(500);",
    "ALTER TABLE users ADD COLUMN persona_keywords TEXT[];",
    "ALTER TABLE users ADD COLUMN persona_source_chapter_count INTEGER;",
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "ALTER TABLE users DROP COLUMN IF EXISTS persona_source_chapter_count;",
    "ALTER TABLE users DROP COLUMN IF EXISTS persona_keywords;",
    "ALTER TABLE users DROP COLUMN IF EXISTS persona_summary;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
