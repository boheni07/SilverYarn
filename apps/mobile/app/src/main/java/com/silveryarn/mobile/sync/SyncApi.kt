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
    /** POST /devices — 설치 시 1회 등록. Device Token이 아직 없는 유일한 예외 호출. */
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

    /** GET /sync/download — sync-contract.md §5, 증분 다운로드. */
    @GET("sync/download")
    suspend fun download(
        @Header("X-Device-Token") deviceToken: String,
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
    val status: String, // success | failed | retrying
    @Json(name = "retry_count") val retryCount: Int,
)

/** GET /sync/download는 design.md §4.1 봉투를 안 쓰고 { "data": {...} }를 바로 감싸는
 * 대신 sync.py가 자체적으로 dict를 반환한다(core_service/modules/sync/api/v1/sync.py
 * download() 참조) — 그래서 이것만 ApiEnvelope가 아니라 직접 파싱한다. */
@JsonClass(generateAdapter = true)
data class SyncDownloadResponse(
    val data: SyncDownloadPayload,
)

@JsonClass(generateAdapter = true)
data class SyncDownloadPayload(
    @Json(name = "sync_version") val syncVersion: String,
    @Json(name = "chapter_updates") val chapterUpdates: List<ChapterUpdate>,
    // sync.py의 download()가 지금은 늘 빈 배열만 채워 보낸다(services/backend README
    // "아직 안 된 것" — GET /sync/download가 여전히 빈 스냅샷 골격). 실제 페이로드
    // 형태가 확정되면 List<Any>를 구체 타입으로 교체.
    @Json(name = "priority_questions") val priorityQuestions: List<Any> = emptyList(),
    @Json(name = "schedule_items") val scheduleItems: List<Any> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class ChapterUpdate(
    @Json(name = "chapter_id") val chapterId: String,
    @Json(name = "chapter_no") val chapterNo: Int,
    val period: String,
    val summary: String,
    val keywords: String,
)
