package com.silveryarn.mobile.photos

import com.silveryarn.mobile.sync.ApiEnvelope
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Url

/**
 * services/backend `photos` 모듈 — sync-contract.md §4 Presigned URL 3단계 흐름.
 * `SyncApi`와 동일한 인증 경로를 쓴다: 어르신 본인 기기는 Device Token
 * (`core_service/auth_deps.py require_principal` → `DeviceIdentity`, design.md §4.2
 * "2FA + Role(family) 또는 Device Token" 중 후자). `authorize_user_access()`가
 * `DeviceIdentity.user_id == 요청 body의 user_id`만 확인하므로, 이 기기가 등록될 때
 * 저장해 둔 `device_state.user_id`(mobile-schema.md v0.12)를 그대로 보낸다.
 */
interface PhotosApi {
    /** POST /photos/upload-url — 1단계, MinIO Presigned PUT URL 발급 + `photos` 행
     * status=pending_upload로 생성. */
    @POST("photos/upload-url")
    suspend fun requestUploadUrl(
        @Header("X-Device-Token") deviceToken: String,
        @Body body: PhotoUploadUrlRequest,
    ): ApiEnvelope<PhotoUploadUrlResponse>

    /** 2단계 — 발급받은 절대 URL(MinIO, 우리 백엔드가 아님)로 압축된 JPEG 바이트를 직접
     * PUT한다. `@Url`이 [com.silveryarn.mobile.sync.RetrofitClient]의 baseUrl을 완전히
     * 대체하므로 이 메서드 호출만 외부 호스트로 나간다(apps/web의
     * `uploadFileToPresignedUrl`과 동일한 Content-Type 헤더 방식). */
    @PUT
    suspend fun putToPresignedUrl(
        @Url uploadUrl: String,
        @Header("Content-Type") contentType: String,
        @Body body: RequestBody,
    ): Response<Unit>

    /** POST /photos/{photoId}/complete — 3단계 업로드 확인 콜백. 멱등 — 재시도해도 안전. */
    @POST("photos/{photoId}/complete")
    suspend fun completeUpload(
        @Header("X-Device-Token") deviceToken: String,
        @Path("photoId") photoId: String,
    ): ApiEnvelope<PhotoCompleteResponse>
}

@JsonClass(generateAdapter = true)
data class PhotoUploadUrlRequest(
    @Json(name = "user_id") val userId: String,
    // schema.md uploader_type enum(family|self) — 모바일은 항상 어르신 본인(self).
    @Json(name = "uploader_type") val uploaderType: String = "self",
    @Json(name = "content_type") val contentType: String,
    @Json(name = "file_size") val fileSize: Int,
)

@JsonClass(generateAdapter = true)
data class PhotoUploadUrlResponse(
    @Json(name = "photo_id") val photoId: String,
    @Json(name = "upload_url") val uploadUrl: String,
    @Json(name = "expires_at") val expiresAt: String,
)

@JsonClass(generateAdapter = true)
data class PhotoCompleteResponse(
    @Json(name = "photo_id") val photoId: String,
    val status: String,
)
