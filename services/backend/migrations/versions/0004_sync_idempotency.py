"""동기화 업로드 멱등성 — conversation_chunks (user_id, session_id, turn_id) 부분 유니크

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-09

SoR: docs/02-design/sync-contract.md §2 (멱등성), CTO Enterprise B1.

## 왜
`POST /sync/upload`가 네트워크 불안정으로 재전송되면 지금은 sync_sessions·arq 잡·
conversation_chunks 행이 중복 생성된다(append-only + 매번 새 uuid). 별도 ULID 컬럼을
추가하는 대신, 이미 있는 `(session_id, turn_id)`(온디바이스 대화 세션 식별자·턴 번호,
schema.md v1.3)로 "한 턴 = 한 행"을 강제한다 — 스키마 컬럼 추가 없음.

부분 인덱스: 두 값이 모두 있는 대화형 업로드에만 적용(비대화형/레거시 업로드는 제외).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    """
    CREATE UNIQUE INDEX uq_conversation_chunks_turn
      ON conversation_chunks (user_id, session_id, turn_id)
      WHERE session_id IS NOT NULL AND turn_id IS NOT NULL;
    """,
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "DROP INDEX IF EXISTS uq_conversation_chunks_turn;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
