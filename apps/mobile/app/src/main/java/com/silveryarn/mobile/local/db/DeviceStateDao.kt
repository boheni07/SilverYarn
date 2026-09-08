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
}
