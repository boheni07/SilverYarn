package com.silveryarn.mobile.local.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/** mobile-schema.md §2.5 `schedule_cache` — 서버 schedule_items(schema.md §3.10)
 * 서브셋 + 온디바이스 자체 생성분(오프라인 등록 후 다음 동기화 시 서버 반영). */
@Entity(tableName = "schedule_cache")
data class ScheduleCacheEntity(
    @PrimaryKey val id: String,
    // "appointment" | "medication"
    val kind: String,
    val description: String?,
    val location: String?,
    // epoch ms
    @ColumnInfo(name = "due_at") val dueAt: Long,
    // pending|confirmed|missed|declined
    val status: String,
    @ColumnInfo(name = "remind_count") val remindCount: Int,
    // "server" | "local" — 로컬 생성분은 동기화 전까지 "local"
    val origin: String,
)
