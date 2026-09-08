package com.silveryarn.mobile.local.db

import androidx.sqlite.db.SimpleSQLiteQuery
import androidx.sqlite.db.SupportSQLiteDatabase

/**
 * `autobiography_fts`(FTS5) 전용 접근 계층 — 일부러 Room `@Dao`가 **아니다**.
 * Room의 KSP 컴파일러는 `@Query`에 쓰인 테이블이 `@Entity`로 알려져 있어야 SQL을
 * 정적 검증할 수 있는데, FTS5 가상테이블은 Room에 전혀 알려져 있지 않다(Room은
 * `@Fts4`까지만 지원, `AutobiographyFts.kt`/`AppDatabase.kt` 주석 참조) — 그래서
 * `@Dao` 인터페이스로 만들면 KSP가 "no such table: autobiography_fts" 컴파일
 * 에러를 낸다. 대신 [SupportSQLiteDatabase]를 직접 받아 raw SQL로 접근한다.
 *
 * `AppDatabase.autobiographyFtsStore()`가 이 클래스를 만들어 준다.
 */
class AutobiographyFtsStore(private val db: SupportSQLiteDatabase) {
    /** mobile-schema.md §2.2 "갱신: ... Upsert" — FTS5엔 UNIQUE 제약이 없어(rowid
     * 기반 가상테이블) delete+insert로 흉내낸다. GET /sync/download의
     * chapter_updates(design.md §4.3)를 그대로 이 컬럼명에 대입해 호출한다. */
    fun upsert(row: AutobiographyFtsRow) {
        db.execSQL("DELETE FROM autobiography_fts WHERE chapter_id = ?", arrayOf(row.chapterId))
        db.execSQL(
            """
            INSERT INTO autobiography_fts (chapter_id, chapter_no, period, summary, keywords)
            VALUES (?, ?, ?, ?, ?)
            """,
            arrayOf(row.chapterId, row.chapterNo, row.period, row.summary, row.keywords),
        )
    }

    /** mobile-schema.md §2.2 조회 예시 그대로 — bm25() 랭킹 함수로 정렬. */
    fun search(query: String, limit: Int = 1): List<AutobiographySearchResult> {
        val sqliteQuery =
            SimpleSQLiteQuery(
                """
                SELECT chapter_id, summary FROM autobiography_fts
                WHERE autobiography_fts MATCH ?
                ORDER BY bm25(autobiography_fts)
                LIMIT ?
                """,
                arrayOf(query, limit),
            )
        return db.query(sqliteQuery).use { cursor ->
            val chapterIdIndex = cursor.getColumnIndexOrThrow("chapter_id")
            val summaryIndex = cursor.getColumnIndexOrThrow("summary")
            buildList {
                while (cursor.moveToNext()) {
                    add(AutobiographySearchResult(cursor.getString(chapterIdIndex), cursor.getString(summaryIndex)))
                }
            }
        }
    }
}
