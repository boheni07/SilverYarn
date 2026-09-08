package com.silveryarn.mobile.local.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/** mobile-schema.md §2.4 `unrecalled_photos` — 서버 photos(schema.md §3.6) 중
 * recall_status='pending' 서브셋. 대화 세션 시작 시 최우선 제시 대상(기획서 4.4절). */
@Entity(tableName = "unrecalled_photos")
data class UnrecalledPhotoEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "storage_ref_local") val storageRefLocal: String,
    val caption: String?,
    @ColumnInfo(name = "year_tag") val yearTag: Int?,
)
