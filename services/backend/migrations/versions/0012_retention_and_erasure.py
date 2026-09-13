"""retention_policies 테이블 + conversation_chunks 보유기간 컬럼 + deletion_records

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-13

SoR: docs/01-plan/decisions/silveryarn-platform.decisions.md #56(2026-09-13
사용자 결정, Q5). `docs/03-check/blocked-decisions-tracker.md` Q5.

## 결정 요약
crypto-shredding을 적법한 파기 수단으로 채택 + 보유기간은 DB 설정 테이블 +
admin 콘솔 UI로 운영자가 직접 조정(하드코딩 금지).

## 실제 스코프 (조사 후 좁힘 — 전체 스키마 재검토 결과)
CTO가 "5개 저장소 통합 삭제"라고 지목했지만, 스키마를 다시 보니 두 가지
성격이 전혀 다른 문제였다:

1. **어르신 계정 전체 삭제(erasure)**: `users` 테이블의 거의 모든 하위 테이블이
   이미 `user_id ... ON DELETE CASCADE`로 걸려 있다(devices, chapters, photos,
   conversation_chunks, questions, schedule_items, emotion_*, consent_logs,
   invitations, **user_encryption_keys 포함**) — `DELETE FROM users`
   한 번으로 Postgres 쪽은 이미 완전히 정리된다(크립토 슈레딩용 키 삭제도
   자동 포함). 이 마이그레이션은 스키마를 안 건드린다 — 이미 되어 있었다.
   남은 건 **Postgres 밖 3곳**(Qdrant·Neo4j·MinIO)의 삭제 오케스트레이션뿐이고,
   이건 스키마가 아니라 코드(`UserErasureService`)의 문제라 여기 없다.

2. **시간 기반 보유기간(retention)**: 원본음성은 이미 업로드 성공 시 즉시
   삭제(decisions #30)이고 챕터·사진은 자서전 결과물이라 계정 존속기간 동안
   보관하는 게 맞다(별도 만료 정책 대상 아님). **실제로 "보유기간"이 의미
   있는 건 conversation_chunks의 원문 대화 텍스트**(챕터로 압축된 뒤엔 원본
   보관 필요성이 낮아짐, CTO가 "최고위험"으로 지목한 벡터도 동일 생명주기)뿐이다.

## 이 마이그레이션이 하는 일
- `retention_policies`(category, retention_days) — 카테고리별 보유기간을
  admin이 조정할 수 있는 설정 테이블. 초기값 `conversation_transcript` = 365일
  (1차 잠정값, admin 콘솔에서 언제든 변경 가능 — 이 숫자 자체는 법무 결정
  사항이 아니라 운영 판단이라 하드코딩하지 않고 여기 넣는 것 자체가 결정이다).
- `conversation_chunks.retention_until`/`purged_at` — 신규 행은 생성 시점에
  그 시점의 정책으로 계산해서 채운다(애플리케이션 코드, `ConversationChunkRepository.create`).
  기존 행은 이 마이그레이션이 백필한다.
- `deletion_records` — 계정 전체 삭제(erasure) 실행 이력. `user_id`가 FK가
  아닌 이유: 이 행이 존재하는 시점엔 그 `users` 행이 이미 없거나(정상 흐름 —
  Postgres 삭제 마지막 단계) 삭제 직전이라, FK를 걸면 순서상 항상 위반된다.
  감사 목적상 삭제된 뒤에도 "누구를, 언제, 왜, 어디까지 지웠는지" 기록이
  남아야 한다(access_logs와 동일 성격 — 도메인 엔티티 아님).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_CONVERSATION_TRANSCRIPT_RETENTION_DAYS = 365

_UPGRADE_STATEMENTS: list[str] = [
    """
    CREATE TABLE retention_policies (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      category VARCHAR(50) NOT NULL UNIQUE,
      retention_days INTEGER NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    f"""
    INSERT INTO retention_policies (category, retention_days)
    VALUES ('conversation_transcript', {_DEFAULT_CONVERSATION_TRANSCRIPT_RETENTION_DAYS});
    """,
    "ALTER TABLE conversation_chunks ADD COLUMN retention_until TIMESTAMPTZ;",
    "ALTER TABLE conversation_chunks ADD COLUMN purged_at TIMESTAMPTZ;",
    # 기존 행 백필 — 신규 행은 애플리케이션 코드가 생성 시점 정책으로 채운다.
    f"""
    UPDATE conversation_chunks
    SET retention_until = created_at + INTERVAL '{_DEFAULT_CONVERSATION_TRANSCRIPT_RETENTION_DAYS} days'
    WHERE retention_until IS NULL;
    """,
    (
        "CREATE INDEX idx_conversation_chunks_retention_until "
        "ON conversation_chunks(retention_until) WHERE purged_at IS NULL;"
    ),
    """
    CREATE TABLE deletion_records (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL,
      requested_by UUID,
      reason VARCHAR(50) NOT NULL,
      purged_stores TEXT[] NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX idx_deletion_records_user_id ON deletion_records(user_id);",
]

_DOWNGRADE_STATEMENTS: list[str] = [
    "DROP TABLE IF EXISTS deletion_records;",
    "DROP INDEX IF EXISTS idx_conversation_chunks_retention_until;",
    "ALTER TABLE conversation_chunks DROP COLUMN IF EXISTS purged_at;",
    "ALTER TABLE conversation_chunks DROP COLUMN IF EXISTS retention_until;",
    "DROP TABLE IF EXISTS retention_policies;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
