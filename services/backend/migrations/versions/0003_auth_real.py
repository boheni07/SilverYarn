"""실 인증 — keycloak_sub 컬럼 + device_credentials + access_logs

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-09

SoR: docs/01-plan/schema.md §5 (v1.8), erd.md §11, cto-review-2026-09-05.md B5, decisions.md #47.

## 무엇을 바꾸나
- `family_members.keycloak_sub` — Keycloak 토큰 `sub` ↔ DB 행 매핑(RBAC 강제 전제, B5(a)).
  **비유일(non-unique) 인덱스**: `family_members.user_id`가 NOT NULL이라 한 사람이 여러
  어르신을 담당하면(복지사·요양보호사) 같은 `sub`로 여러 행이 생긴다 — erd.md §11의
  "UK 컬럼" 제안과 달리 UNIQUE를 걸지 않는 이유(decisions.md #47).
- `device_credentials` — Device Token 발급·회전·폐기(B5(b)). 평문 토큰은 발급 시 1회만
  응답에 담고 서버는 SHA-256 해시만 보관.
- `access_logs` — 접속기록 감사로그(「개인정보의 안전성 확보조치 기준」제8조, B5(e)).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    "ALTER TABLE family_members ADD COLUMN keycloak_sub VARCHAR(255);",
    "CREATE INDEX idx_family_members_keycloak_sub ON family_members(keycloak_sub);",
    """
    CREATE TABLE device_credentials (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
      token_hash VARCHAR(64) NOT NULL UNIQUE,
      issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      last_used_at TIMESTAMPTZ,
      revoked_at TIMESTAMPTZ
    );
    """,
    "CREATE INDEX idx_device_credentials_device ON device_credentials(device_id);",
    "CREATE TYPE access_actor_kind AS ENUM ('family_member', 'device', 'anonymous');",
    """
    CREATE TABLE access_logs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      actor_kind access_actor_kind NOT NULL,
      actor_subject VARCHAR(255),
      method VARCHAR(10) NOT NULL,
      path VARCHAR(500) NOT NULL,
      status_code SMALLINT NOT NULL,
      client_ip VARCHAR(64),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX idx_access_logs_created ON access_logs(created_at DESC);",
    "CREATE INDEX idx_access_logs_subject ON access_logs(actor_subject, created_at DESC);",
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "DROP TABLE IF EXISTS access_logs;",
    "DROP TYPE IF EXISTS access_actor_kind;",
    "DROP TABLE IF EXISTS device_credentials;",
    "DROP INDEX IF EXISTS idx_family_members_keycloak_sub;",
    "ALTER TABLE family_members DROP COLUMN IF EXISTS keycloak_sub;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
