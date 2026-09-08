package com.silveryarn.mobile.local.db

/**
 * mobile-schema.md §2.2 `autobiography_fts` — Zero-Neural RAG(decisions.md #32,
 * Phase 1 기본값)의 핵심 테이블. Room에는 FTS5 전용 어노테이션이 없어(`@Fts4`만
 * 지원) [AppDatabase]의 `RoomDatabase.Callback.onCreate`에서 문서 DDL 그대로
 * raw SQL로 만든다 — 그래서 이 파일엔 `@Entity`가 없다. `chapter_id`가 PK 역할을
 * 하지만 FTS5 가상테이블은 진짜 PK 제약을 못 걸어(rowid 기반) [AutobiographyFtsStore]의
 * upsert가 delete+insert로 흉내낸다.
 */
data class AutobiographyFtsRow(
    val chapterId: String,
    val chapterNo: Int,
    val period: String,
    val summary: String,
    val keywords: String,
)

/** BM25 검색 결과 — MATCH 쿼리 결과 컬럼만 담는 최소 프로젝션. */
data class AutobiographySearchResult(
    val chapterId: String,
    val summary: String,
)

internal const val CREATE_AUTOBIOGRAPHY_FTS_SQL =
    """
    CREATE VIRTUAL TABLE autobiography_fts USING fts5(
        chapter_id UNINDEXED,
        chapter_no UNINDEXED,
        period UNINDEXED,
        summary,
        keywords,
        tokenize = 'unicode61'
    )
    """
