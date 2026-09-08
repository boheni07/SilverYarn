package com.silveryarn.mobile.local.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/** mobile-schema.md §2.1 `conversations` — 서버 conversation_chunks(schema.md §3.8)의
 * 로컬 버퍼. id는 로컬 생성 UUID를 서버 업로드 시 그대로 멱등성 키로 재사용한다. */
@Entity(tableName = "conversations")
data class ConversationEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "turn_id") val turnId: Int,
    val mode: String, // "author" | "care" | "assist"
    @ColumnInfo(name = "user_query") val userQuery: String,
    @ColumnInfo(name = "assistant_response") val assistantResponse: String,
    @ColumnInfo(name = "audio_path") val audioPath: String?, // 업로드 성공 시 null로 초기화(decisions.md #30)
    @ColumnInfo(name = "linked_chapter_id") val linkedChapterId: String?,
    @ColumnInfo(name = "response_latency_ms") val responseLatencyMs: Int?,
    @ColumnInfo(name = "sync_status") val syncStatus: String, // PENDING|UPLOADING|SYNCED|FAILED
    @ColumnInfo(name = "created_at") val createdAt: Long, // epoch ms
)
