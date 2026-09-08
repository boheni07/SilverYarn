package com.silveryarn.mobile.installmode

import android.app.ActivityManager
import android.content.Context
import android.os.Build

/**
 * 실기기에서 [InstallModeResolver]에 넣을 값(총 RAM, Android SDK 버전)을 읽어온다 —
 * 순수 판별 로직(InstallModeResolver)과 Android 프레임워크 의존 IO를 분리해,
 * 로직만 JVM 유닛테스트로 검증 가능하게 했다(services/backend와 동일한 도메인/
 * 인프라 분리 원칙, structure.md §2).
 */
class DeviceCapabilityReader(
    private val context: Context,
) {
    fun resolveInstallMode(): InstallMode {
        val ramGb = totalRamGb()
        return InstallModeResolver.resolve(ramGb, Build.VERSION.SDK_INT)
    }

    private fun totalRamGb(): Double {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        return memoryInfo.totalMem.toDouble() / (1024.0 * 1024.0 * 1024.0)
    }
}
