"""PII 2차 — contact 암호문+blind index, birth_date 앱 레이어 암호화

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-09

SoR: docs/01-plan/schema.md §5 (v1.11), decisions.md #45(2차), CTO 검토 B4.

## 무엇을 바꾸나
- `family_members.contact` / `invitations.contact`: VARCHAR(100) → VARCHAR(255)
  (Fernet 토큰이 100자를 넘음). 저장값이 암호문이 되고, 동등검색용 `contact_bidx`
  (HMAC-SHA256 hex, core/crypto.py) 컬럼 + 인덱스를 추가한다.
- `users.birth_date`: DATE → VARCHAR(200) (앱 레이어 암호화 토큰 보관). 쿼리 필터에
  쓰이지 않으므로 타입만 바꾸면 된다 — 기존 DATE 값은 `::text`로 옮겨두고(평문),
  다음 저장 때 암호화된다(core/crypto.py의 `pii.v1.` 접두사 검사).
- `name`은 **평문 유지**(decisions.md #45 2차 — 부분검색 UX·낮은 민감도).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    "ALTER TABLE users ALTER COLUMN birth_date TYPE VARCHAR(200) USING birth_date::text;",
    "ALTER TABLE family_members ALTER COLUMN contact TYPE VARCHAR(255);",
    "ALTER TABLE family_members ADD COLUMN contact_bidx VARCHAR(64);",
    "CREATE INDEX idx_family_members_contact_bidx ON family_members(contact_bidx);",
    "ALTER TABLE invitations ALTER COLUMN contact TYPE VARCHAR(255);",
    "ALTER TABLE invitations ADD COLUMN contact_bidx VARCHAR(64);",
    "CREATE INDEX idx_invitations_contact_bidx ON invitations(contact_bidx);",
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "DROP INDEX IF EXISTS idx_invitations_contact_bidx;",
    "ALTER TABLE invitations DROP COLUMN IF EXISTS contact_bidx;",
    "ALTER TABLE invitations ALTER COLUMN contact TYPE VARCHAR(100);",
    "DROP INDEX IF EXISTS idx_family_members_contact_bidx;",
    "ALTER TABLE family_members DROP COLUMN IF EXISTS contact_bidx;",
    "ALTER TABLE family_members ALTER COLUMN contact TYPE VARCHAR(100);",
    # birth_date는 되돌리지 않는다 — 암호문이 섞여 있으면 DATE 캐스팅이 실패한다.
    # 롤백이 필요하면 별도 복호화 스크립트 후 수동 전환.
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
