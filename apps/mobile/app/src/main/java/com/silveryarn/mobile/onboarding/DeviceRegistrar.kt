package com.silveryarn.mobile.onboarding

import android.content.Context
import android.os.Build
import com.silveryarn.mobile.auth.DeviceCredentialStore
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.local.db.DeviceStateEntity
import com.silveryarn.mobile.sync.DeviceRegisterRequest
import com.silveryarn.mobile.sync.RetrofitClient

/**
 * `POST /devices` 1회 등록(design.md §2.9 온보딩, decisions.md #5·#47).
 *
 * 서버가 하는 일: install_mode 판정(RAM/OS 임계값) + Device Token 발급(응답에 1회).
 * 이 클래스가 하는 일: 응답의 토큰을 [DeviceCredentialStore]에, device_id/install_mode를
 * Room `device_state`에 저장 → 이후 [com.silveryarn.mobile.sync.SyncWorker]가 동작 가능.
 *
 * 호출 시점은 온보딩에서 어르신 계정(user_id) 생성 직후다 — [OnboardingCoordinator.run]
 * 3연쇄의 두 번째 단계.
 */
class DeviceRegistrar(private val context: Context) {
    /**
     * @param userId  온보딩에서 만든 어르신(1차 사용자) 계정 id
     * @param userName 어르신 이름 — 서버가 등록 응답에 되돌려주지 않아 호출자가 그대로 넘긴다
     *   (device_state.user_name, mobile-schema.md v0.10 — 홈 화면 인사말용)
     * @param displayId 표시용 기기 ID(예: "MB-1042") — 발급 규칙은 운영 정책, 지금은 호출자가 결정
     * @param ramGb 총 RAM(GB) — install_mode 판정 입력(DeviceCapabilityReader가 읽는 값)
     * @return 성공 시 서버 device_id
     */
    suspend fun register(
        userId: String,
        userName: String,
        displayId: String,
        ramGb: Double,
        modelName: String? = Build.MODEL,
        androidVersion: String = Build.VERSION.RELEASE,
    ): Result<String> =
        runCatching {
            val response =
                RetrofitClient.syncApi.registerDevice(
                    DeviceRegisterRequest(
                        displayId = displayId,
                        modelName = modelName,
                        userId = userId,
                        ramGb = ramGb,
                        androidVersion = androidVersion,
                    ),
                )
            val device = response.data ?: error("등록 응답이 비어 있습니다.")
            val token = device.deviceToken ?: error("등록 응답에 device_token이 없습니다.")

            DeviceCredentialStore.getInstance(context).saveToken(token)
            AppDatabase.getInstance(context).deviceStateDao().upsert(
                DeviceStateEntity(
                    deviceId = device.id,
                    installMode = device.installMode,
                    registeredWifiSsid = null,
                    slmModelVersion = device.slmModelVersion,
                    promptPackVersion = device.promptPackVersion,
                    lastSyncAt = null,
                    lastSyncVersion = null,
                    userName = userName,
                ),
            )
            device.id
        }
}
