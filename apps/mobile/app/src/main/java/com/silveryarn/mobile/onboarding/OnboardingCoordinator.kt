package com.silveryarn.mobile.onboarding

import android.content.Context
import com.silveryarn.mobile.auth.DeviceCredentialStore
import com.silveryarn.mobile.installmode.DeviceCapabilityReader
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.sync.RetrofitClient
import kotlin.random.Random

/**
 * 온보딩 서버 3연쇄: `POST /users` → `POST /devices`(토큰·install_mode 발급) →
 * `POST /users/{id}/consent-logs`.
 *
 * 순서 이유: 동의 기록(recordConsent)은 `X-Device-Token`이 필요하고
 * (consent_logs.py의 require_principal), 그 토큰은 `POST /devices` 응답으로만 나온다.
 * 사용자에게는 동의 화면을 **먼저** 보여주고 '동의' 후에 이 3연쇄를 한 번에 돌린다 —
 * UI상 "수집 전 동의"는 지켜지고 API 호출 순서는 구현 세부사항이다.
 */
class OnboardingCoordinator(
    private val context: Context,
) {
    private val registrar = DeviceRegistrar(context)
    private val capabilities = DeviceCapabilityReader(context)

    /**
     * @param name 어르신 이름(필수)
     * @param birthDate ISO `yyyy-MM-dd` 또는 null
     * @return 성공 시 서버가 판정한 `install_mode`("kiosk"|"normal")
     */
    suspend fun run(
        name: String,
        birthDate: String?,
    ): Result<String> =
        runCatching {
            val user =
                RetrofitClient.onboardingApi
                    .createUser(UserCreateRequest(name = name.trim(), birthDate = birthDate?.ifBlank { null }))
                    .data ?: error("사용자 생성 응답이 비어 있습니다.")

            // 임시 display_id — 발급 규칙은 운영 정책(DeviceRegistrar 주석 참조).
            val displayId = "MB-%04d".format(Random.nextInt(0, 10000))
            registrar
                .register(
                    userId = user.id,
                    userName = name.trim(),
                    displayId = displayId,
                    ramGb = capabilities.totalRamGb(),
                ).getOrThrow()

            val token =
                DeviceCredentialStore.getInstance(context).token()
                    ?: error("Device Token이 저장되지 않았습니다.")
            RetrofitClient.onboardingApi.recordConsent(
                deviceToken = token,
                userId = user.id,
                body =
                    ConsentRecordRequest(
                        consentType = ConsentTypes.DATA_COLLECTION,
                        granted = true,
                    ),
            )

            AppDatabase.getInstance(context).deviceStateDao().get()?.installMode ?: "normal"
        }
}
