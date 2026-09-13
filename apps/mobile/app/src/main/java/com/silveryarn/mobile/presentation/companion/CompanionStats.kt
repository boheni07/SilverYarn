package com.silveryarn.mobile.presentation.companion

import android.content.Context
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.local.db.UnrecalledPhotoEntity
import java.time.LocalDate

/** 은실이가 대화를 시작할 때 참고하는 로컬 데이터 — 예전 홈 화면(M2, 하단탭 제거로
 * 폐지)의 `HomeStats`를 그대로 옮겨왔다. 화면 자체는 없어졌지만 "과거를 아는" 첫
 * 인사말을 만드는 데 이 값들이 그대로 쓰인다. */
data class CompanionStats(
    val userName: String?,
    val completedChapters: Int,
    val conversationStreakDays: Int,
    val unrecalledPhotoCount: Int,
    val nextQuestion: String?,
    val nextUnrecalledPhoto: UnrecalledPhotoEntity?,
)

/** 전부 로컬 DB 조회만 — 오프라인에서도 인사말이 완결 동작해야 한다(design.md §2.1). */
suspend fun loadCompanionStats(context: Context): CompanionStats {
    val db = AppDatabase.getInstance(context)
    val deviceState = db.deviceStateDao().get()
    val completedChapters = db.autobiographyFtsStore().countChapters()
    val unrecalledPhotoCount = db.unrecalledPhotoDao().count()
    val nextQuestion = db.questionCacheDao().listUnanswered().firstOrNull()?.text
    val nextUnrecalledPhoto = db.unrecalledPhotoDao().peekNext()
    val streakDays = computeStreakDays(db.conversationDao().listDistinctLocalDates())
    return CompanionStats(
        userName = deviceState?.userName,
        completedChapters = completedChapters,
        conversationStreakDays = streakDays,
        unrecalledPhotoCount = unrecalledPhotoCount,
        nextQuestion = nextQuestion,
        nextUnrecalledPhoto = nextUnrecalledPhoto,
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

/**
 * 은실이의 첫 인사말 — 서버가 내려준 우선 질문(questions_cache) > 미회고 사진 >
 * 연속 대화일수 > 기본 인사 순으로, "먼저 기억을 꺼내 묻는" 컨셉(사용자 요청)을
 * 실제 로컬 데이터로 채운다.
 */
fun companionGreeting(stats: CompanionStats?): String {
    val name = stats?.userName
    val question = stats?.nextQuestion
    if (question != null) {
        return "안녕하세요${nameSuffix(name)}. 저는 은실이예요. $question"
    }
    val photo = stats?.nextUnrecalledPhoto
    if (photo != null) {
        val year = photo.yearTag?.let { "${it}년 " } ?: ""
        return "안녕하세요${nameSuffix(name)}. 저는 은실이예요. 지난번에 올려주신 ${year}사진 이야기를 좀 더 들려주실래요?"
    }
    val streak = stats?.conversationStreakDays ?: 0
    if (streak > 0) {
        return "안녕하세요${nameSuffix(name)}. 오늘로 ${streak}일째 저와 이야기해 주고 계시네요."
    }
    return "안녕하세요${nameSuffix(name)}. 저는 은실이예요. 오늘 하루는 어떠셨어요?"
}

private fun nameSuffix(name: String?): String = if (name != null) ", ${name}님" else ", 어르신"
