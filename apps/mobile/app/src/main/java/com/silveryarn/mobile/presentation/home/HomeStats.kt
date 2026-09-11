package com.silveryarn.mobile.presentation.home

import android.content.Context
import com.silveryarn.mobile.local.db.AppDatabase
import java.time.LocalDate

/** 홈 화면(M2) 요약 통계 바 + 인사 헤더 + 회고 질문 카드가 쓰는 값 —
 * UI/UX 화면설계서 M2 요소 1·3·4. */
data class HomeStats(
    val userName: String?,
    val completedChapters: Int,
    val conversationStreakDays: Int,
    val unrecalledPhotoCount: Int,
    val nextQuestion: String?,
)

/** 전부 로컬 DB 조회만 — 오프라인에서도 홈 화면이 완결 동작해야 한다(design.md §2.1). */
suspend fun loadHomeStats(context: Context): HomeStats {
    val db = AppDatabase.getInstance(context)
    val deviceState = db.deviceStateDao().get()
    val completedChapters = db.autobiographyFtsStore().countChapters()
    val unrecalledPhotoCount = db.unrecalledPhotoDao().count()
    val nextQuestion = db.questionCacheDao().listUnanswered().firstOrNull()?.text
    val streakDays = computeStreakDays(db.conversationDao().listDistinctLocalDates())
    return HomeStats(
        userName = deviceState?.userName,
        completedChapters = completedChapters,
        conversationStreakDays = streakDays,
        unrecalledPhotoCount = unrecalledPhotoCount,
        nextQuestion = nextQuestion,
    )
}

/**
 * 오늘(또는 오늘 대화가 아직 없으면 어제)부터 거슬러 하루도 빠짐없이 이어진 날짜 수.
 * `dates`는 "yyyy-MM-dd" 문자열 — 순서는 무관(Set으로 변환해 사용).
 */
private fun computeStreakDays(dates: List<String>): Int {
    if (dates.isEmpty()) return 0
    val dateSet = dates.map(LocalDate::parse).toHashSet()
    var cursor = LocalDate.now()
    if (cursor !in dateSet) cursor = cursor.minusDays(1)
    var streak = 0
    while (cursor in dateSet) {
        streak++
        cursor = cursor.minusDays(1)
    }
    return streak
}
