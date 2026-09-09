"""PII 필드 암호화 — user_encryption_keys 테이블 추가

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-09

SoR: docs/01-plan/schema.md §5 (v1.5 — user_encryption_keys 부속 테이블), decisions.md #45,
docs/02-design/cto-review-2026-09-05.md B4.

## 무엇을 바꾸나
- `user_encryption_keys` 테이블 신설: 사용자별 DEK를 KEK로 랩핑해 보관.
- 암호화 대상 컬럼(`chapters.body_text`, `chapter_revisions.body_text_snapshot`,
  `conversation_chunks.transcript_on_device` / `transcript_server` / `assistant_response`)은
  **타입 변경이 없다** — Fernet 토큰은 ASCII라 기존 TEXT 컬럼에 그대로 들어간다.
  암복호화는 애플리케이션(core/crypto.py + repository 계층)이 전담한다.

## 기존 데이터
운영 데이터는 없다. 로컬 개발 DB의 기존 평문 행은 core/crypto.py의 `pii.v1.` 접두사
검사 덕분에 복호화 시 그대로 읽히고, 다음 저장(재감수·재업로드) 때 암호화된다.
일괄 백필이 필요하면 별도 스크립트로 처리한다(이 마이그레이션 범위 밖).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    """
    CREATE TABLE user_encryption_keys (
      user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
      dek_wrapped BYTEA NOT NULL,
      key_version SMALLINT NOT NULL DEFAULT 1,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "DROP TABLE IF EXISTS user_encryption_keys;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
