package com.silveryarn.mobile.sync

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * services/backend 실 엔드포인트와 1:1 매핑 — 서버 쪽 Pydantic 요청/응답 모델
 * (core_service/modules/{devices,sync}/api/v1 아래의 *.py)을 그대로 옮겼다. 필드가
 * 갈라지면 여기와 서버 둘 중 하나가 낡은 것이니 서버 코드를 SoR로 맞춘다.
 */
interface SyncApi {
    /** POST /devices — 설치 시 1회 등록(인증 없는 부트스트랩). 응답의 `deviceToken`은
     *  이 호출에서만 평문으로 내려온다(서버는 SHA-256 해시만 보관, decisions.md #47) —
     *  이후 모든 sync 요청의 `X-Device-Token` 헤더에 쓴다. 안전한 저장소(Keystore
     *  기반 EncryptedSharedPreferences 등)에 보관해야 한다 — 후속 과제. */
    @POST("devices")
    suspend fun registerDevice(
        @Body body: DeviceRegisterRequest,
    ): ApiEnvelope<DeviceResponse>

    /** POST /sync/upload — sync-contract.md §2.1, 202 Accepted 비동기 접수. */
    @POST("sync/upload")
    suspend fun uploadSession(
        @Header("X-Device-Token") deviceToken: String,
        @Body body: SyncUploadRequest,
    ): ApiEnvelope<SyncUploadAccepted>

    /** GET /sync/sessions/{sessionId} — sync-contract.md §2.2, 업로드 작업 상태 폴링. */
    @GET("sync/sessions/{sessionId}")
    suspend fun getSessionStatus(
        @Header("X-Device-Token") deviceToken: String,
        @Path("sessionId") sessionId: String,
    ): ApiEnvelope<SyncSessionStatusResponse>

    /** GET /sync/download — sync-contract.md §5, 증분 다운로드.
     *
     * device_id는 필수 쿼리 파라미터(sync-contract.md v0.3 신규) — Device Token
     * 자체가 아직 특정 기기를 검증 못 하는 스텁이라 서버가 호출 주체를 알 방법이
     * 이것뿐이다. */
    @GET("sync/download")
    suspend fun download(
        @Header("X-Device-Token") deviceToken: String,
        @Query("device_id") deviceId: String,
        @Query("since") since: String? = null,
    ): SyncDownloadResponse
}

@JsonClass(generateAdapter = true)
data class DeviceRegisterRequest(
    @Json(name = "display_id") val displayId: String,
    @Json(name = "model_name") val modelName: String?,
    @Json(name = "user_id") val userId: String,
    @Json(name = "ram_gb") val ramGb: Double,
    @Json(name = "android_version") val androidVersion: String,
)

@JsonClass(generateAdapter = true)
data class DeviceResponse(
    val id: String,
    @Json(name = "display_id") val displayId: String,
    @Json(name = "install_mode") val installMode: String,
    @Json(name = "slm_model_version") val slmModelVersion: String?,
    @Json(name = "prompt_pack_version") val promptPackVersion: String?,
    // POST /devices 응답에만 존재(decisions.md #47) — 재조회로는 얻을 수 없다.
    @Json(name = "device_token") val deviceToken: String? = null,
)

@JsonClass(generateAdapter = true)
data class SyncUploadRequest(
    @Json(name = "device_id") val deviceId: String,
    val checksum: String,
    @Json(name = "raw_audio_ref") val rawAudioRef: String,
    @Json(name = "transcript_on_device") val transcriptOnDevice: String,
    val mode: String?,
    @Json(name = "device_session_id") val deviceSessionId: String?,
    @Json(name = "turn_id") val turnId: Int?,
)

@JsonClass(generateAdapter = true)
data class SyncUploadAccepted(
    @Json(name = "session_id") val sessionId: String,
    @Json(name = "job_id") val jobId: String,
)

@JsonClass(generateAdapter = true)
data class SyncSessionStatusResponse(
    @Json(name = "session_id") val sessionId: String,
    // success | failed | retrying
    val status: String,
    @Json(name = "retry_count") val retryCount: Int,
)

/** GET /sync/download는 design.md §4.1 봉투를 안 쓰고 { "data": {...} }를 바로 감싸는
 * 대신 sync.py가 DataResponse[SyncDownloadResponse](서버 쪽 이름이 같아 헷갈리지만
 * core_service/modules/sync/api/v1/sync.py의 SyncDownloadResponse)로 반환한다 —
 * 그래서 이것만 ApiEnvelope가 아니라 직접 파싱한다. */
@JsonClass(generateAdapter = true)
data class SyncDownloadResponse(
    val data: SyncDownloadPayload,
)

@JsonClass(generateAdapter = true)
data class SyncDownloadPayload(
    @Json(name = "sync_version") val syncVersion: String,
    @Json(name = "chapter_updates") val chapterUpdates: List<ChapterUpdate>,
    @Json(name = "priority_questions") val priorityQuestions: List<PriorityQuestion> = emptyList(),
    @Json(name = "schedule_items") val scheduleItems: List<ScheduleItemDownload> = emptyList(),
    // design.md §2.11 4단계 "단기 압축 기억" — 요약된 챕터가 하나도 없으면 null.
    // chapter_updates와 달리 diff가 아니라 매번 최신값 전체(sync-contract.md §5).
    @Json(name = "persona_snapshot") val personaSnapshot: PersonaSnapshot? = null,
)

@JsonClass(generateAdapter = true)
data class PersonaSnapshot(
    val summary: String,
    val keywords: List<String> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class ChapterUpdate(
    @Json(name = "chapter_id") val chapterId: String,
    @Json(name = "chapter_no") val chapterNo: Int,
    val period: String,
    // sync-contract.md §5 v0.3 — Compaction Engine(design.md §2.11) 미구현이라
    // 서버가 body_text 원문을 그대로 보낸다(요약 아님). keywords는 항상 빈 배열.
    val summary: String,
    val keywords: List<String> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class PriorityQuestion(
    @Json(name = "question_id") val questionId: String,
    @Json(name = "linked_chapter_id") val linkedChapterId: String?,
    val text: String,
    // "new_topic" | "follow_up"
    val type: String,
)

@JsonClass(generateAdapter = true)
data class ScheduleItemDownload(
    val id: String,
    // "appointment" | "medication"
    val kind: String,
    @Json(name = "due_at") val dueAt: String,
    val description: String?,
)
