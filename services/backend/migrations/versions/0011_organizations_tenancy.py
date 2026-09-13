"""organizations 테이블 + users/family_members.org_id (B2G 시설 테넌시 안전망)

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-13

SoR: docs/01-plan/decisions/silveryarn-platform.decisions.md #59(2026-09-12
사용자 결정, I2). erd.md §11(그동안 "⏸️ 보류" 상태였던 항목).

## 무엇을 바꾸나
CTO 검토 B5(c) — "조직/시설 엔티티 없음(B2G 시설간 열람차단 불가)". 사용자 결정
(2026-09-13): 기존 1:1 `family_members` 연결(admin 중개 초대, decisions #51)은
그대로 유지하고, `organizations`는 그 위에 얹는 **안전망(defense-in-depth)**으로만
쓴다 — 시설 소속 직원(caregiver/social_worker)의 `org_id`와 어르신(`users.org_id`)의
`org_id`가 다르면, 설령 개별 초대가 잘못 발급됐더라도 차단한다. B2G 대량 권한
부여 모델(조직원이 조직 소속 어르신 전체를 자동 조회)은 이번 라운드 범위 밖 —
그건 정식 B2G 운영모델이 확정된 뒤의 더 큰 작업이다.

- `organizations` — id, name, created_at만. 주소·사업자번호 등은 B2G 운영모델
  확정 후 필요에 따라 추가(YAGNI).
- `users.org_id` — NULL 허용(B2C 개인 사용자는 계속 NULL). 어르신이 어느 시설
  소속인지.
- `family_members.org_id` — NULL 허용(가족은 계속 NULL, 개인 소속 없음). 직원이
  어느 시설 소속인지.
- `invitations.org_id` — 시설 소속 직원을 초대할 때 그 소속을 실어 나르는 용도
  (수락 시점에 `family_members.org_id`로 그대로 옮겨진다). 초대 자체엔 영구적
  의미가 없어 `family_members`/`users`처럼 별도 인덱스는 두지 않는다.

전부 `ON DELETE SET NULL` — 시설이 삭제돼도 사용자/직원/초대 행 자체는 남는다
(시설 소속만 해제).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    """
    CREATE TABLE organizations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(200) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "ALTER TABLE users ADD COLUMN org_id UUID REFERENCES organizations(id) ON DELETE SET NULL;",
    ("ALTER TABLE family_members ADD COLUMN org_id UUID REFERENCES organizations(id) ON DELETE SET NULL;"),
    "ALTER TABLE invitations ADD COLUMN org_id UUID REFERENCES organizations(id) ON DELETE SET NULL;",
    "CREATE INDEX idx_users_org_id ON users(org_id);",
    "CREATE INDEX idx_family_members_org_id ON family_members(org_id);",
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "DROP INDEX IF EXISTS idx_family_members_org_id;",
    "DROP INDEX IF EXISTS idx_users_org_id;",
    "ALTER TABLE invitations DROP COLUMN IF EXISTS org_id;",
    "ALTER TABLE family_members DROP COLUMN IF EXISTS org_id;",
    "ALTER TABLE users DROP COLUMN IF EXISTS org_id;",
    "DROP TABLE IF EXISTS organizations;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
