package com.silveryarn.mobile.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.local.db.AutobiographyFtsRow
import com.silveryarn.mobile.local.db.QuestionCacheEntity
import com.silveryarn.mobile.local.db.ScheduleCacheEntity
import java.time.Instant

/**
 * Wi-Fi 배치 동기화 워커 — decisions.md 확정 항목("등록 Wi-Fi 한정, 접속 즉시 자동
 * 트리거, 데이터 제한 없음"). 실제 트리거 등록(ConnectivityManager.NetworkCallback +
 * 등록 SSID 비교, decisions.md #22)은 아직 없다 — 이 워커는 WorkManager가 실제로
 * 실행할 작업 단위(PENDING 대화 업로드 → download 폴링)만 정의한다.
 *
 * TODO(Do 단계):
 * - Wi-Fi 등록 SSID 매칭 후 enqueue하는 트리거 로직(installmode 또는 별도 net/ 패키지)
 * - Device Token 발급·저장 위치 확정(erd.md §11 device_credentials 후보, 결정 대기 —
 *   device_id는 mobile-schema.md v0.4로 device_state에 저장하지만, "인증 토큰" 자체는
 *   아직 별도 컬럼/보안저장소가 없다. core/auth.py의 require_device_token도 지금은
 *   아무 문자열이나 통과하는 스텁이라 서버 쪽도 같이 확정돼야 함)
 * - checksum 계산(원본 오디오 sha256, SYNC_CHECKSUM_ALGO와 일치)
 * - raw_audio_ref 업로드 계약(sync/upload는 아직 원본 업로드 자체가 없어 —
 *   services/backend README "아직 안 된 것" — 로컬 파일 경로를 그대로 보낼 수 없다.
 *   photos 모듈의 Presigned URL 흐름처럼 확정되면 교체)
 */
class SyncWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val db = AppDatabase.getInstance(applicationContext)
        val deviceState = db.deviceStateDao().get() ?: return Result.failure()
        val deviceId = deviceState.deviceId ?: return Result.failure() // 아직 등록 전(POST /devices 미완료)
        val pending = db.conversationDao().listPendingSync()

        for (conversation in pending) {
            val audioPath = conversation.audioPath ?: continue // 이미 업로드돼 정리된 행은 건너뜀
            runCatching {
                RetrofitClient.syncApi.uploadSession(
                    // TODO: 위 클래스 docstring 참조 — 아직 실 토큰 발급 경로가 없음
                    deviceToken = "",
                    body =
                        SyncUploadRequest(
                            deviceId = deviceId,
                            // TODO: 위 클래스 docstring 참조
                            checksum = "",
                            // TODO: 위 클래스 docstring 참조
                            rawAudioRef = audioPath,
                            transcriptOnDevice = conversation.userQuery,
                            mode = conversation.mode,
                            deviceSessionId = conversation.sessionId,
                            turnId = conversation.turnId,
                        ),
                )
            }.onSuccess {
                db.conversationDao().markSyncedAndClearAudio(conversation.id)
            }
        }

        applyDownload(db, deviceId, deviceState.lastSyncVersion)

        return Result.success()
    }

    /** GET /sync/download 결과를 로컬 캐시에 반영 — sync-contract.md §5.
     *
     * chapter_updates → autobiography_fts(FTS5 Upsert), priority_questions →
     * questions_cache, schedule_items → schedule_cache. 실패해도 upload는 이미
     * 끝났으니 워커 전체를 실패시키지 않는다(runCatching — 다음 주기에 다시 시도). */
    private suspend fun applyDownload(
        db: AppDatabase,
        deviceId: String,
        since: String?,
    ) {
        runCatching {
            RetrofitClient.syncApi.download(
                // TODO: 위 클래스 docstring 참조 — 아직 실 토큰 발급 경로가 없음
                deviceToken = "",
                deviceId = deviceId,
                since = since,
            )
        }.onSuccess { response ->
            val payload = response.data

            for (chapter in payload.chapterUpdates) {
                db.autobiographyFtsStore().upsert(
                    AutobiographyFtsRow(
                        chapterId = chapter.chapterId,
                        chapterNo = chapter.chapterNo,
                        period = chapter.period,
                        summary = chapter.summary,
                        // FTS5 unicode61 토크나이저는 공백 구분 토큰이라 join(" ")으로 충분
                        keywords = chapter.keywords.joinToString(" "),
                    ),
                )
            }

            db.questionCacheDao().upsertAll(
                payload.priorityQuestions.mapIndexed { index, question ->
                    QuestionCacheEntity(
                        id = question.questionId,
                        linkedChapterId = question.linkedChapterId,
                        text = question.text,
                        type = question.type,
                        answered = false, // 서버가 이미 미답변만 골라 보낸다(question_repository.py)
                        priority = index,
                    )
                },
            )

            for (item in payload.scheduleItems) {
                db.scheduleCacheDao().upsert(
                    ScheduleCacheEntity(
                        id = item.id,
                        kind = item.kind,
                        description = item.description,
                        location = null, // 서버 응답엔 없음(design.md §4.3 예시에도 없음)
                        dueAt = Instant.parse(item.dueAt).toEpochMilli(),
                        status = "pending", // 서버가 이미 pending만 골라 보낸다(schedule_item_repository.py)
                        remindCount = 0,
                        origin = "server",
                    ),
                )
            }

            db.deviceStateDao().updateLastSync(
                epochMs = System.currentTimeMillis(),
                syncVersion = payload.syncVersion,
            )
        }
    }
}
