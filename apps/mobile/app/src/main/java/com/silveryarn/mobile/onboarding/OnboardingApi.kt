package com.silveryarn.mobile.onboarding

import com.silveryarn.mobile.sync.ApiEnvelope
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

/**
 * 온보딩 흐름(design.md §2.9)의 서버 호출 — `core_service/modules/{users,consent}/api/v1`와
 * 1:1 매핑. `sync/SyncApi.kt`와 동일한 규약(Moshi `@JsonClass` codegen, 필드별 `@Json(name=)`).
 *
 * 온보딩 순서(design.md §2.9): 설치모드 자동분기 → 초기설정(이름) → **createUser** →
 * **recordConsent(data_collection)** → 가족 초대(invitations) → 최초 Wi-Fi 동기화.
 *
 * ⚠️ 실제 화면 연결(네비게이션·상태 관리)은 아직 미구현 — `OnboardingScreen.kt` 참조.
 * 이 파일은 서버 계약을 먼저 고정해 두는 것이 목적이다(SyncApi.kt와 동일 접근).
 */
interface OnboardingApi {
    /** POST /users — 어르신(1차 사용자) 계정 생성. 아직 토큰이 없는 부트스트랩 호출
     *  (서버 `POST /users`도 인증 의존성이 없다 — users/api/v1/users.py). */
    @POST("users")
    suspend fun createUser(
        @Body body: UserCreateRequest,
    ): ApiEnvelope<UserResponse>

    /** POST /users/{userId}/consent-logs — 개인정보 수집 동의/철회 1건 기록.
     *
     *  인가: 서버는 "2FA + Role(family) 또는 Device Token"(require_auth_or_device_token).
     *  온보딩 중 어르신 본인 동의는 기기가 자신의 X-Device-Token으로 보낸다
     *  (granted_by 없음 = self). 실 Device Token 발급은 B5(device_credentials) 후속 과제라
     *  현재 서버 검증은 스텁(비어 있지 않기만 하면 통과). */
    @POST("users/{userId}/consent-logs")
    suspend fun recordConsent(
        @Header("X-Device-Token") deviceToken: String,
        @Path("userId") userId: String,
        @Body body: ConsentRecordRequest,
    ): ApiEnvelope<ConsentLogResponse>
}

@JsonClass(generateAdapter = true)
data class UserCreateRequest(
    val name: String,
    @Json(name = "birth_date") val birthDate: String? = null,
)

@JsonClass(generateAdapter = true)
data class UserResponse(
    val id: String,
    val name: String,
    @Json(name = "birth_date") val birthDate: String?,
    @Json(name = "primary_device_id") val primaryDeviceId: String?,
)

@JsonClass(generateAdapter = true)
data class ConsentRecordRequest(
    // "data_collection" | "external_tts_optin" | "external_llm_optin"
    @Json(name = "consent_type") val consentType: String,
    val granted: Boolean,
    @Json(name = "granted_by") val grantedBy: String? = null,
)

@JsonClass(generateAdapter = true)
data class ConsentLogResponse(
    val id: String,
    @Json(name = "user_id") val userId: String,
    @Json(name = "consent_type") val consentType: String,
    val granted: Boolean,
    // "self" | "proxy" — 서버가 granted_by 유무에서 파생(CTO 검토 B2)
    val actor: String,
    @Json(name = "granted_at") val grantedAt: String,
)

/** 온보딩에서 쓰는 동의 유형 상수 — 서버 `consent_type` enum과 일치. */
object ConsentTypes {
    const val DATA_COLLECTION = "data_collection"
    const val EXTERNAL_TTS_OPTIN = "external_tts_optin"
    const val EXTERNAL_LLM_OPTIN = "external_llm_optin"
}
