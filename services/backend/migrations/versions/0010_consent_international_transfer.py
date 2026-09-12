"""consent_type enum에 international_transfer 값 추가

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-13

SoR: docs/01-plan/decisions/silveryarn-platform.decisions.md #57(2026-09-12
사용자 결정, Q6). `docs/03-check/blocked-decisions-tracker.md` Q6.

## 무엇을 바꾸나
FCM(구글, 미국 서버) 유지 결정에 따라 푸시알림 발송 시 기기토큰이 국외로
이전된다 — 개인정보보호법상 국외이전 고지·동의 대상으로 보고, 데이터수집
동의(`data_collection`)와 구분되는 별도 동의 유형 `international_transfer`를
`consent_type` enum(마이그레이션 0001, 0009에서 이미 한 번 증분)에 추가한다.

## Postgres 제약
마이그레이션 0009와 동일 — `ALTER TYPE ... ADD VALUE`는 PG12+에서 트랜잭션
안에서 실행 가능하지만 같은 트랜잭션에서 그 값을 바로 쓸 수는 없다(이 마이그레이션은
추가만 하므로 문제없음). enum 값 제거는 Postgres가 지원하지 않아 downgrade는
no-op이다.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE consent_type ADD VALUE IF NOT EXISTS 'international_transfer';")


def downgrade() -> None:
    # Postgres는 enum 값 제거를 지원하지 않는다 — 0009와 동일 사유로 no-op.
    pass
