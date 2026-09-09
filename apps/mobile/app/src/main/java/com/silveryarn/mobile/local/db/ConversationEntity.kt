package com.silveryarn.mobile.local.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/** mobile-schema.md §2.1 `conversations` — 서버 conversation_chunks(schema.md §3.8)의
 * 로컬 버퍼. id는 로컬 생성 UUID.
 *
 * 업로드 멱등성 키는 이 id가 아니라 `(session_id, turn_id)`다(sync-contract.md §2.3):
 * 서버가 `POST /sync/upload` body의 `device_session_id`/`turn_id`로 dedup하고
 * `uq_conversation_chunks_turn` 부분 유니크 인덱스로 강제한다 — 재전송/잡 재시도해도
 * 한 턴은 한 행. (id 자체는 서버로 보내지 않으므로 멱등성 키가 될 수 없다.) */
@Entity(tableName = "conversations")
data class ConversationEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "turn_id") val turnId: Int,
    // "author" | "care" | "assist"
    val mode: String,
    @ColumnInfo(name = "user_query") val userQuery: String,
    @ColumnInfo(name = "assistant_response") val assistantResponse: String,
    // 업로드 성공 시 null로 초기화(decisions.md #30)
    @ColumnInfo(name = "audio_path") val audioPath: String?,
    @ColumnInfo(name = "linked_chapter_id") val linkedChapterId: String?,
    @ColumnInfo(name = "response_latency_ms") val responseLatencyMs: Int?,
    // PENDING|UPLOADING|SYNCED|FAILED
    @ColumnInfo(name = "sync_status") val syncStatus: String,
    // epoch ms
    @ColumnInfo(name = "created_at") val createdAt: Long,
)
