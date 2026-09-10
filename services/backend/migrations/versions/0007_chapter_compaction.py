"""챕터 Compaction Engine — 온디바이스 FTS5용 요약·키워드

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-10

SoR: docs/02-design/features/silveryarn-platform.design.md §2.11(4단계 Compaction
Engine), docs/02-design/sync-contract.md §5, schema.md §5.

## 무엇을 바꾸나
`chapters`에 온디바이스 SQLite FTS5(`autobiography_fts`, mobile-schema.md §2.2)로
내려보낼 **요약·키워드**를 보관하는 3개 컬럼을 추가한다. `GET /sync/download`의
`chapter_updates.summary`/`keywords`가 이 값을 그대로 쓴다(이전엔 `body_text`
원문/빈 배열로 대체).

- `compaction_summary`  VARCHAR(500) NULL — vLLM이 만든 2문장 이내 요약
- `compaction_keywords` TEXT[]        NULL — 핵심 키워드 5~10개
- `compacted_version`   INTEGER       NULL — 요약 시점의 `chapters.version`.
    `version`과 다르면(또는 NULL이면) 요약이 stale — 파이프라인이 재계산한다.

`compaction_summary`가 NULL이면 아직 요약 안 됨(신규 챕터, 또는 vLLM 미가동) —
`sync/download`는 그 경우 `body_text`를 잘라서 임시로 내려보낸다.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    "ALTER TABLE chapters ADD COLUMN compaction_summary VARCHAR(500);",
    "ALTER TABLE chapters ADD COLUMN compaction_keywords TEXT[];",
    "ALTER TABLE chapters ADD COLUMN compacted_version INTEGER;",
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "ALTER TABLE chapters DROP COLUMN IF EXISTS compacted_version;",
    "ALTER TABLE chapters DROP COLUMN IF EXISTS compaction_keywords;",
    "ALTER TABLE chapters DROP COLUMN IF EXISTS compaction_summary;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
