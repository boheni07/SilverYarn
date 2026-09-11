package com.silveryarn.mobile.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface DeviceStateDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(state: DeviceStateEntity)

    @Query("SELECT * FROM device_state WHERE id = 0")
    suspend fun get(): DeviceStateEntity?

    @Query("UPDATE device_state SET last_sync_at = :epochMs WHERE id = 0")
    suspend fun updateLastSyncAt(epochMs: Long)

    /** SyncWorker의 download() 성공 직후 호출 — 다음 호출의 since 커서(mobile-schema.md v0.5). */
    @Query("UPDATE device_state SET last_sync_at = :epochMs, last_sync_version = :syncVersion WHERE id = 0")
    suspend fun updateLastSync(
        epochMs: Long,
        syncVersion: String,
    )

    /** download() 응답의 persona_snapshot 로컬 캐시(mobile-schema.md v0.11) — null이면
     * (아직 요약된 챕터 없음) 기존 값을 지운다. */
    @Query("UPDATE device_state SET persona_summary = :summary, persona_keywords = :keywords WHERE id = 0")
    suspend fun updatePersonaSnapshot(
        summary: String?,
        keywords: String?,
    )
}
