package com.silveryarn.mobile.sync

import android.content.Context
import com.silveryarn.mobile.auth.DeviceCredentialStore
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.local.db.AutobiographyFtsRow
import com.silveryarn.mobile.local.db.QuestionCacheEntity
import com.silveryarn.mobile.local.db.ScheduleCacheEntity
import java.io.File
import java.security.MessageDigest
import java.time.Instant

/** 한 번의 Wi-Fi 배치 동기화 결과. */
sealed interface SyncOutcome {
    /** 업로드 루프가 돌았고 download를 시도했다. [downloadApplied]가 false면 download 단계에서
     * 예외가 났지만(다음 주기 재시도) 업로드는 이미 반영됐다는 뜻. */
    data class Completed(
        val uploaded: Int,
        val downloadApplied: Boolean,
    ) : SyncOutcome

    /** `device_state.device_id` 또는 Device Token이 없다 — 온보딩(DeviceRegistrar)이 먼저 돌아야 한다.
     * 재시도해도 소용없다. */
    object NotRegistered : SyncOutcome
}

/**
 * 동기화 로직 본체 — [SyncWorker](WorkManager 예약 실행)와 최초 동기화 화면
 * (`presentation/sync/FirstSyncScreen`, 온보딩 직후 1회)이 공유한다. Worker에서 떼어낸 이유:
 * 온보딩 완료 화면이 "첫 동기화 중…" 진행 상태를 보여주려면 같은 절차를 화면에서도
 * 직접 호출할 수 있어야 하고, 로직이 `CoroutineWorker` 밖에 있으면 JVM 유닛테스트도 쉽다.
 *
 * 인증: [DeviceCredentialStore]의 Device Token을 `X-Device-Token`으로 보낸다(decisions.md #47).
 * 절차: PENDING 대화 업로드 → `GET /sync/download` 결과를 로컬 캐시(FTS5/questions_cache/
 * schedule_cache)에 반영(sync-contract.md §2·§5).
 */
class SyncRunner(
    private val context: Context,
) {
    suspend fun runOnce(): SyncOutcome {
        val db = AppDatabase.getInstance(context)
        val deviceState = db.deviceStateDao().get() ?: return SyncOutcome.NotRegistered
        val deviceId = deviceState.deviceId ?: return SyncOutcome.NotRegistered
        val deviceToken =
            DeviceCredentialStore.getInstance(context).token() ?: return SyncOutcome.NotRegistered

        val pending = db.conversationDao().listPendingSync()
        var uploaded = 0
        for (conversation in pending) {
            val audioPath = conversation.audioPath ?: continue // 이미 업로드돼 정리된 행은 건너뜀
            val uploadResult =
                runCatching {
                    RetrofitClient.syncApi.uploadSession(
                        deviceToken = deviceToken,
                        body =
                            SyncUploadRequest(
                                deviceId = deviceId,
                                checksum = fileSha256OrEmpty(audioPath),
                                rawAudioRef = audioPath,
                                transcriptOnDevice = conversation.userQuery,
                                mode = conversation.mode,
                                deviceSessionId = conversation.sessionId,
                                turnId = conversation.turnId,
                            ),
                    )
                }
            if (uploadResult.isSuccess) {
                db.conversationDao().markSyncedAndClearAudio(conversation.id)
                uploaded += 1
            }
        }

        val downloadApplied = applyDownload(db, deviceId, deviceToken, deviceState.lastSyncVersion)
        return SyncOutcome.Completed(uploaded = uploaded, downloadApplied = downloadApplied)
    }

    /** 원본 오디오 파일의 SHA-256(hex) — SYNC_CHECKSUM_ALGO와 일치. 파일이 없거나 읽기 실패 시
     * 빈 문자열(서버가 아직 값을 검증하지 않으므로 업로드 자체는 진행). */
    private fun fileSha256OrEmpty(path: String): String =
        runCatching {
            val digest = MessageDigest.getInstance("SHA-256")
            File(path).inputStream().use { stream ->
                val buffer = ByteArray(8192)
                var read = stream.read(buffer)
                while (read >= 0) {
                    digest.update(buffer, 0, read)
                    read = stream.read(buffer)
                }
            }
            digest.digest().joinToString("") { "%02x".format(it.toInt() and 0xFF) }
        }.getOrDefault("")

    /** `GET /sync/download` 결과를 로컬 캐시에 반영 — sync-contract.md §5. 예외가 나면 false를
     * 반환하되 던지지 않는다(업로드는 이미 끝났으니 다음 주기에 다시 시도). */
    private suspend fun applyDownload(
        db: AppDatabase,
        deviceId: String,
        deviceToken: String,
        since: String?,
    ): Boolean =
        runCatching {
            val response =
                RetrofitClient.syncApi.download(
                    deviceToken = deviceToken,
                    deviceId = deviceId,
                    since = since,
                )
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
                        // 서버가 이미 미답변만 골라 보낸다(question_repository.py)
                        answered = false,
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
                        // 서버 응답엔 없음(design.md §4.3 예시에도 없음)
                        location = null,
                        dueAt = Instant.parse(item.dueAt).toEpochMilli(),
                        // 서버가 이미 pending만 골라 보낸다(schedule_item_repository.py)
                        status = "pending",
                        remindCount = 0,
                        origin = "server",
                    ),
                )
            }

            db.deviceStateDao().updateLastSync(
                epochMs = System.currentTimeMillis(),
                syncVersion = payload.syncVersion,
            )
            true
        }.getOrDefault(false)
}
