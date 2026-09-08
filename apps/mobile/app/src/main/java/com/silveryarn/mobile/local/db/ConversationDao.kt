package com.silveryarn.mobile.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update

@Dao
interface ConversationDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(conversation: ConversationEntity)

    @Update
    suspend fun update(conversation: ConversationEntity)

    @Query("SELECT * FROM conversations WHERE sync_status = 'PENDING' ORDER BY created_at ASC")
    suspend fun listPendingSync(): List<ConversationEntity>

    /** mobile-schema.md §3 retention 정책 — 업로드 200 OK 수신 시 오디오 파일 경로만
     * null로 비운다(파일 삭제 자체는 sync 워커 책임, decisions.md #30). */
    @Query("UPDATE conversations SET audio_path = NULL, sync_status = 'SYNCED' WHERE id = :id")
    suspend fun markSyncedAndClearAudio(id: String)

    /** mobile-schema.md §3 — 매일 자정 배치가 5일(잠정, decisions.md #9) 지난 행을 정리. */
    @Query("DELETE FROM conversations WHERE created_at < :cutoffEpochMs")
    suspend fun deleteOlderThan(cutoffEpochMs: Long)
}
