"""consent_type enum에 third_party_access 값 추가

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-12

SoR: docs/01-plan/decisions/silveryarn-platform.decisions.md #54(2026-09-12
사용자 결정, Q3). `docs/03-check/blocked-decisions-tracker.md` Q3.

## 무엇을 바꾸나
복지사(social_worker)의 어르신 데이터(챕터·사진·대화·일정) 열람을 CTO 검토가
"제17조 제3자제공인가, 제26조 위탁범위 내 이용인가" 법무 질문으로 지목했었다
(decisions.md #48). #54에서 **가족=위탁범위 내 이용(별도 동의 불필요), 복지사=
제3자제공(전용 동의 필요)**으로 확정 — 이 전용 동의를 표현할 `consent_type` 값
`third_party_access`를 `consent_logs` 테이블이 이미 쓰고 있는 Postgres ENUM
타입 `consent_type`(마이그레이션 0001)에 추가한다.

## 왜 새 테이블이 아니라 기존 enum에 추가만 하나
`consent_logs`는 이미 (user_id, consent_type, granted, granted_by, granted_at)
불변 로그 구조를 갖고 있어 새로운 동의 유형을 표현하는 데 스키마 변경이
컬럼이 아니라 enum 값 추가만으로 충분하다.

## Postgres 제약
`ALTER TYPE ... ADD VALUE`는 PG12+부터 트랜잭션 안에서 실행 가능하지만, **같은
트랜잭션에서 그 값을 바로 사용할 수는 없다**(이 마이그레이션은 값을 추가만 하고
쓰지 않으므로 문제없다). enum 값 제거는 Postgres가 지원하지 않아 downgrade는
값을 실제로 없애지 못한다 — 타입을 통째로 재생성해야 하는데, 이미 그 값으로
기록된 행이 있을 수 있어 위험한 작업이라 downgrade는 의도적으로 no-op이다.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE consent_type ADD VALUE IF NOT EXISTS 'third_party_access';")


def downgrade() -> None:
    # Postgres는 enum 값 제거를 지원하지 않는다(타입 재생성 필요, 기존 데이터 위험).
    # 이 값을 실제로 쓰는 행이 생기면 되돌릴 수 없다는 뜻이므로 의도적으로 no-op.
    pass
