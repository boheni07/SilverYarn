package com.silveryarn.mobile.installmode

/**
 * decisions.md #5 설치모드 판별 임계값 — RAM 6GB 미만 **또는** Android 11(API 30)
 * 이하 → 키오스크, 그 외 일반. 둘 중 하나라도 미달 시 보수적으로 키오스크 판정.
 *
 * ⚠️ services/backend의 `determine_install_mode()`
 * (core_service/modules/devices/domain/device.py)와 반드시 같은 값을 유지해야 한다
 * — 서버가 `POST /devices`에서도 독립적으로 같은 규칙을 적용해 최종 판정하므로,
 * 여기서 어긋나도 서버가 정정하긴 하지만(서버가 SoR) 기기 쪽 UI가 잘못된 모드를
 * 먼저 보여주는 사용자 경험 버그로 이어질 수 있다.
 */
enum class InstallMode {
    KIOSK,
    NORMAL,
}

object InstallModeResolver {
    private const val KIOSK_RAM_THRESHOLD_GB = 6.0
    private const val KIOSK_MAX_ANDROID_SDK_INT = 30 // Android 11

    fun resolve(
        ramGb: Double,
        androidSdkInt: Int,
    ): InstallMode =
        if (ramGb < KIOSK_RAM_THRESHOLD_GB || androidSdkInt <= KIOSK_MAX_ANDROID_SDK_INT) {
            InstallMode.KIOSK
        } else {
            InstallMode.NORMAL
        }
}
