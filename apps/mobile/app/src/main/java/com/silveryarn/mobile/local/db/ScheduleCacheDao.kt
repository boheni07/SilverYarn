package com.silveryarn.mobile.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface ScheduleCacheDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(item: ScheduleCacheEntity)

    @Query("SELECT * FROM schedule_cache WHERE status = 'pending' ORDER BY due_at ASC")
    suspend fun listPending(): List<ScheduleCacheEntity>

    /** 다음 동기화 때 서버로 올릴 대상 — 오프라인 중 온디바이스에서 직접 등록된 것. */
    @Query("SELECT * FROM schedule_cache WHERE origin = 'local'")
    suspend fun listUnsyncedLocal(): List<ScheduleCacheEntity>

    @Query("UPDATE schedule_cache SET remind_count = remind_count + 1 WHERE id = :id")
    suspend fun incrementRemindCount(id: String)

    @Query("UPDATE schedule_cache SET status = :status WHERE id = :id")
    suspend fun updateStatus(
        id: String,
        status: String,
    )
}
