package com.silveryarn.mobile.installmode

import android.app.Activity
import android.app.ActivityManager
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context

/**
 * install_mode="kiosk"일 때 COSU lockTask(화면 고정) 진입/해제 — decisions.md #6
 * (Device Owner Mode, Screen Pinning 미채택).
 *
 * 앱이 Device Owner가 아니면(개발 빌드·일반 설치) lockTask를 걸 수 없으므로 조용히
 * 아무 것도 하지 않는다 — 키오스크 UX는 안 되지만 앱은 정상 동작한다. 실기기
 * zero-touch/QR 프로비저닝으로 Device Owner가 설정된 경우에만 실제로 잠긴다.
 *
 * ⚠️ lockTask 화이트리스트(이 앱 패키지만 허용)는 Device Owner 설정 시점
 * ([SilverYarnDeviceAdminReceiver] onEnabled 또는 프로비저닝 스크립트)에 별도로
 * `setLockTaskPackages`로 등록돼 있어야 `startLockTask()`가 사용자 확인 다이얼로그
 * 없이 바로 잠긴다.
 */
class KioskController(
    private val activity: Activity,
) {
    private val dpm: DevicePolicyManager =
        activity.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager

    private val adminComponent =
        ComponentName(activity, SilverYarnDeviceAdminReceiver::class.java)

    /** [installMode]가 "kiosk"면 lockTask 진입을 시도하고, 아니면 혹시 걸려 있던 lockTask를 푼다. */
    fun apply(installMode: String) {
        if (installMode == INSTALL_MODE_KIOSK) {
            enterKiosk()
        } else {
            exitKiosk()
        }
    }

    private fun enterKiosk() {
        if (!dpm.isDeviceOwnerApp(activity.packageName)) return
        runCatching {
            dpm.setLockTaskPackages(adminComponent, arrayOf(activity.packageName))
            if (!isInLockTask()) {
                activity.startLockTask()
            }
        }
    }

    private fun exitKiosk() {
        runCatching {
            if (isInLockTask()) {
                activity.stopLockTask()
            }
        }
    }

    private fun isInLockTask(): Boolean {
        val am = activity.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        // minSdk 26 — lockTaskModeState(API 23+)는 항상 사용 가능
        return am.lockTaskModeState != ActivityManager.LOCK_TASK_MODE_NONE
    }

    companion object {
        const val INSTALL_MODE_KIOSK = "kiosk"
    }
}
