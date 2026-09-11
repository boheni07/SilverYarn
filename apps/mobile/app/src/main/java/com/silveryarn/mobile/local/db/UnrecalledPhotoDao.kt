package com.silveryarn.mobile.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface UnrecalledPhotoDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(photos: List<UnrecalledPhotoEntity>)

    /** 대화 세션 시작 시 최우선 제시(기획서 4.4절) — 가장 먼저 큐에 들어온 것부터. */
    @Query("SELECT * FROM unrecalled_photos ORDER BY rowid ASC LIMIT 1")
    suspend fun peekNext(): UnrecalledPhotoEntity?

    @Query("DELETE FROM unrecalled_photos WHERE id = :id")
    suspend fun remove(id: String)

    @Query("DELETE FROM unrecalled_photos")
    suspend fun clear()

    /** 홈 화면(M2) "미회고 사진" 통계용. */
    @Query("SELECT COUNT(*) FROM unrecalled_photos")
    suspend fun count(): Int
}
