package com.silveryarn.mobile.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface QuestionCacheDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(questions: List<QuestionCacheEntity>)

    /** 미회고 사진 큐가 있으면 그보다 후순위(mobile-schema.md §2.3 priority 설명) —
     * 실제 우선순위 병합은 온디바이스 라우터(ondevice/) 책임, 여기서는 저장된 순서만 반환. */
    @Query("SELECT * FROM questions_cache WHERE answered = 0 ORDER BY priority ASC")
    suspend fun listUnanswered(): List<QuestionCacheEntity>

    @Query("UPDATE questions_cache SET answered = 1 WHERE id = :id")
    suspend fun markAnswered(id: String)

    @Query("DELETE FROM questions_cache")
    suspend fun clear()
}
