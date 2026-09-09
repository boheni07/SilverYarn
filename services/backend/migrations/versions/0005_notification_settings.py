"""notification_settings — 채널 UNIQUE + 정서 알림 기본값 opt-out

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-09

SoR: docs/01-plan/schema.md §3.15/§5, CTO 검토 B1.

## 무엇을 바꾸나
- `uq_notification_settings_member_channel (family_member_id, channel)` — 한 구성원이
  같은 채널로 2개 설정을 갖지 못하게(모듈 구현 중 필요 확인, schema.md v1.10).
- `receives_emotion_alerts` 기본값 `true` → `false`. CTO 보안 검토 B1: 정서(민감정보
  인접) 알림은 opt-out(기본 수신)이 아니라 opt-in이어야 한다.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UPGRADE_STATEMENTS: list[str] = [
    """
    CREATE UNIQUE INDEX uq_notification_settings_member_channel
      ON notification_settings (family_member_id, channel);
    """,
    "ALTER TABLE notification_settings ALTER COLUMN receives_emotion_alerts SET DEFAULT false;",
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "ALTER TABLE notification_settings ALTER COLUMN receives_emotion_alerts SET DEFAULT true;",
    "DROP INDEX IF EXISTS uq_notification_settings_member_channel;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
