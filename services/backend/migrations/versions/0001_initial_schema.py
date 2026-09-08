"""initial schema — schema.md v1.4 DDL 1:1 반영 (17개 엔티티)

Revision ID: 0001
Revises:
Create Date: 2026-09-07

SoR: docs/01-plan/schema.md §5. 이 마이그레이션과 schema.md가 다르면 schema.md를 먼저
갱신하고 이 파일을 다시 생성한다(신규 revision으로, 기존 파일을 손으로 고치지 않는다).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# schema.md §5 DDL을 그대로 옮긴 개별 구문들 — asyncpg가 단일 실행문에서
# 다중 SQL 문을 지원하지 않으므로 op.execute()를 문장 단위로 호출한다.
_UPGRADE_STATEMENTS: list[str] = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
    """
    CREATE TABLE users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(100) NOT NULL,
      birth_date DATE,
      primary_device_id UUID,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE TYPE family_role AS ENUM ('family', 'caregiver', 'social_worker', 'admin');",
    """
    CREATE TABLE family_members (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      role family_role NOT NULL,
      name VARCHAR(100) NOT NULL,
      contact VARCHAR(100) NOT NULL,
      two_factor_enabled BOOLEAN NOT NULL DEFAULT false,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE TYPE install_mode AS ENUM ('kiosk', 'normal');",
    """
    CREATE TABLE devices (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      display_id VARCHAR(20) NOT NULL UNIQUE,
      model_name VARCHAR(50),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      ram_gb NUMERIC(4,1) NOT NULL,
      android_version VARCHAR(20) NOT NULL,
      install_mode install_mode NOT NULL,
      ai_tops NUMERIC(5,1),
      slm_model_version VARCHAR(50),
      prompt_pack_version VARCHAR(50),
      installed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      last_sync_at TIMESTAMPTZ
    );
    """,
    """
    ALTER TABLE users
      ADD CONSTRAINT fk_users_primary_device
      FOREIGN KEY (primary_device_id) REFERENCES devices(id) ON DELETE SET NULL;
    """,
    "CREATE TYPE chapter_period AS ENUM ('childhood', 'youth', 'adulthood', 'present');",
    "CREATE TYPE chapter_status AS ENUM ('draft', 'in_review', 'rejected', 'confirmed');",
    """
    CREATE TABLE chapters (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      chapter_no SMALLINT NOT NULL,
      title VARCHAR(200) NOT NULL,
      period chapter_period NOT NULL,
      body_text TEXT NOT NULL,
      status chapter_status NOT NULL DEFAULT 'draft',
      version INTEGER NOT NULL DEFAULT 1,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE (user_id, chapter_no)
    );
    """,
    "CREATE TYPE revision_action AS ENUM ('approved', 'rejected');",
    """
    CREATE TABLE chapter_revisions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
      version INTEGER NOT NULL,
      body_text_snapshot TEXT NOT NULL,
      reviewer_id UUID REFERENCES family_members(id),
      review_comment TEXT,
      action revision_action NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE TYPE uploader_type AS ENUM ('family', 'self');",
    "CREATE TYPE recall_status AS ENUM ('pending', 'completed');",
    "CREATE TYPE placement_status AS ENUM ('proposed', 'confirmed');",
    "CREATE TYPE quality_flag AS ENUM ('ok', 'blurry', 'inappropriate', 'unreviewed');",
    """
    CREATE TABLE photos (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      uploader_type uploader_type NOT NULL,
      storage_ref VARCHAR(500) NOT NULL,
      caption VARCHAR(300),
      year_tag SMALLINT,
      recall_status recall_status NOT NULL DEFAULT 'pending',
      placement_status placement_status NOT NULL DEFAULT 'proposed',
      inline_position VARCHAR(50),
      linked_chunk_id UUID,
      linked_chapter_id UUID REFERENCES chapters(id),
      quality_flag quality_flag NOT NULL DEFAULT 'unreviewed',
      width SMALLINT,
      height SMALLINT,
      file_size_kb INTEGER,
      mime_type VARCHAR(20),
      uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE TYPE photo_request_status AS ENUM ('pending', 'fulfilled', 'dismissed');",
    """
    CREATE TABLE photo_requests (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      requested_by UUID REFERENCES family_members(id),
      message VARCHAR(300),
      status photo_request_status NOT NULL DEFAULT 'pending',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      fulfilled_at TIMESTAMPTZ
    );
    """,
    "CREATE TYPE conversation_mode AS ENUM ('author', 'care', 'assist');",
    """
    CREATE TABLE conversation_chunks (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      raw_audio_ref VARCHAR(500) NOT NULL,
      transcript_on_device TEXT NOT NULL,
      transcript_server TEXT,
      meta_period VARCHAR(20),
      meta_people TEXT[],
      meta_place VARCHAR(100),
      meta_emotion VARCHAR(50),
      meta_prosody JSONB,
      linked_photo_id UUID REFERENCES photos(id),
      embedding_id VARCHAR(100),
      graph_node_ref VARCHAR(100),
      session_id VARCHAR(100),
      turn_id INTEGER,
      mode conversation_mode,
      assistant_response TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    """
    ALTER TABLE photos
      ADD CONSTRAINT fk_photos_linked_chunk
      FOREIGN KEY (linked_chunk_id) REFERENCES conversation_chunks(id);
    """,
    "CREATE TYPE question_type AS ENUM ('new_topic', 'follow_up');",
    """
    CREATE TABLE questions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      linked_chapter_id UUID REFERENCES chapters(id),
      text TEXT NOT NULL,
      type question_type NOT NULL,
      answered BOOLEAN NOT NULL DEFAULT false,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE TYPE schedule_kind AS ENUM ('appointment', 'medication');",
    "CREATE TYPE schedule_status AS ENUM ('pending', 'confirmed', 'missed', 'declined');",
    """
    CREATE TABLE schedule_items (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      kind schedule_kind NOT NULL,
      description VARCHAR(300),
      location VARCHAR(200),
      recurrence VARCHAR(50),
      due_at TIMESTAMPTZ NOT NULL,
      status schedule_status NOT NULL DEFAULT 'pending',
      remind_count SMALLINT NOT NULL DEFAULT 0,
      next_remind_at TIMESTAMPTZ,
      decline_reason VARCHAR(300),
      responded_at TIMESTAMPTZ
    );
    """,
    """
    CREATE TABLE emotion_alerts (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      score NUMERIC(5,2) NOT NULL,
      triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      acknowledged_by UUID REFERENCES family_members(id),
      acknowledged_at TIMESTAMPTZ,
      closed_at TIMESTAMPTZ
    );
    """,
    """
    CREATE TABLE emotion_scores (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      recorded_date DATE NOT NULL,
      score NUMERIC(5,2) NOT NULL,
      note VARCHAR(300),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE (user_id, recorded_date)
    );
    """,
    "CREATE TYPE sync_direction AS ENUM ('upload', 'download');",
    "CREATE TYPE sync_status AS ENUM ('success', 'failed', 'retrying');",
    """
    CREATE TABLE sync_sessions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
      direction sync_direction NOT NULL,
      status sync_status NOT NULL,
      checksum VARCHAR(128) NOT NULL,
      retry_count SMALLINT NOT NULL DEFAULT 0,
      started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      finished_at TIMESTAMPTZ
    );
    """,
    "CREATE TYPE consent_type AS ENUM ('data_collection', 'external_tts_optin', 'external_llm_optin');",
    """
    CREATE TABLE consent_logs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      consent_type consent_type NOT NULL,
      granted BOOLEAN NOT NULL,
      granted_by UUID REFERENCES family_members(id),
      granted_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE TYPE notify_channel AS ENUM ('sms', 'email', 'push');",
    """
    CREATE TABLE notification_settings (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      family_member_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
      channel notify_channel NOT NULL,
      receives_emotion_alerts BOOLEAN NOT NULL DEFAULT true,
      receives_chapter_updates BOOLEAN NOT NULL DEFAULT true,
      receives_sync_issues BOOLEAN NOT NULL DEFAULT false,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    "CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'expired');",
    """
    CREATE TABLE invitations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      invited_by UUID REFERENCES family_members(id),
      contact VARCHAR(100) NOT NULL,
      role family_role NOT NULL,
      token VARCHAR(100) NOT NULL UNIQUE,
      status invitation_status NOT NULL DEFAULT 'pending',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      expires_at TIMESTAMPTZ NOT NULL
    );
    """,
    "CREATE TYPE publication_format AS ENUM ('hardcover_pdf', 'epub');",
    "CREATE TYPE publication_status AS ENUM ('requested', 'processing', 'ready', 'delivered');",
    """
    CREATE TABLE publications (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      format publication_format NOT NULL,
      status publication_status NOT NULL DEFAULT 'requested',
      storage_ref VARCHAR(500),
      requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      completed_at TIMESTAMPTZ
    );
    """,
    "CREATE INDEX idx_chapters_user ON chapters(user_id);",
    "CREATE INDEX idx_photos_user_recall ON photos(user_id, recall_status);",
    "CREATE INDEX idx_chunks_user ON conversation_chunks(user_id);",
    "CREATE INDEX idx_schedule_user_due ON schedule_items(user_id, due_at);",
    "CREATE INDEX idx_sync_device ON sync_sessions(device_id, started_at DESC);",
    # apps/admin 전체 기기 통합 모니터링(신규, 2026-09-08) — 기기 하나로 필터하지 않고
    # 전체 sync_sessions를 started_at DESC로 훑는 쿼리 전용. idx_sync_device는 device_id
    # 선두 컬럼이라 이 정렬에는 못 쓰인다. users 목록과 달리 sync_sessions는 Wi-Fi 배치
    # 동기화마다 계속 쌓이는 고성장 테이블이라 Seq Scan을 감수하지 않기로 했다.
    "CREATE INDEX idx_sync_started_at ON sync_sessions(started_at DESC);",
    "CREATE INDEX idx_emotion_scores_user_date ON emotion_scores(user_id, recorded_date DESC);",
    "CREATE INDEX idx_devices_display_id ON devices(display_id);",
]

# 역순 정리 — FK/의존관계 역순으로 DROP
_DOWNGRADE_STATEMENTS: list[str] = [
    "DROP TABLE IF EXISTS publications;",
    "DROP TYPE IF EXISTS publication_status;",
    "DROP TYPE IF EXISTS publication_format;",
    "DROP TABLE IF EXISTS invitations;",
    "DROP TYPE IF EXISTS invitation_status;",
    "DROP TABLE IF EXISTS notification_settings;",
    "DROP TYPE IF EXISTS notify_channel;",
    "DROP TABLE IF EXISTS consent_logs;",
    "DROP TYPE IF EXISTS consent_type;",
    "DROP TABLE IF EXISTS sync_sessions;",
    "DROP TYPE IF EXISTS sync_status;",
    "DROP TYPE IF EXISTS sync_direction;",
    "DROP TABLE IF EXISTS emotion_scores;",
    "DROP TABLE IF EXISTS emotion_alerts;",
    "DROP TABLE IF EXISTS schedule_items;",
    "DROP TYPE IF EXISTS schedule_status;",
    "DROP TYPE IF EXISTS schedule_kind;",
    "DROP TABLE IF EXISTS questions;",
    "DROP TYPE IF EXISTS question_type;",
    "ALTER TABLE photos DROP CONSTRAINT IF EXISTS fk_photos_linked_chunk;",
    "DROP TABLE IF EXISTS conversation_chunks;",
    "DROP TYPE IF EXISTS conversation_mode;",
    "DROP TABLE IF EXISTS photo_requests;",
    "DROP TYPE IF EXISTS photo_request_status;",
    "DROP TABLE IF EXISTS photos;",
    "DROP TYPE IF EXISTS quality_flag;",
    "DROP TYPE IF EXISTS placement_status;",
    "DROP TYPE IF EXISTS recall_status;",
    "DROP TYPE IF EXISTS uploader_type;",
    "DROP TABLE IF EXISTS chapter_revisions;",
    "DROP TYPE IF EXISTS revision_action;",
    "DROP TABLE IF EXISTS chapters;",
    "DROP TYPE IF EXISTS chapter_status;",
    "DROP TYPE IF EXISTS chapter_period;",
    "ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_primary_device;",
    "DROP TABLE IF EXISTS devices;",
    "DROP TYPE IF EXISTS install_mode;",
    "DROP TABLE IF EXISTS family_members;",
    "DROP TYPE IF EXISTS family_role;",
    "DROP TABLE IF EXISTS users;",
]


def upgrade() -> None:
    for stmt in _UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _DOWNGRADE_STATEMENTS:
        op.execute(stmt)
