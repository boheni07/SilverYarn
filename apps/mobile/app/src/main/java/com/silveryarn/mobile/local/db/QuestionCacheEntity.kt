package com.silveryarn.mobile.local.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/** mobile-schema.md §2.3 `questions_cache` — 서버 questions(schema.md §3.9) 서브셋.
 * GET /sync/download의 priority_questions로 갱신. */
@Entity(tableName = "questions_cache")
data class QuestionCacheEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "linked_chapter_id") val linkedChapterId: String?,
    val text: String,
    // "new_topic" | "follow_up"
    val type: String,
    val answered: Boolean,
    val priority: Int,
)
