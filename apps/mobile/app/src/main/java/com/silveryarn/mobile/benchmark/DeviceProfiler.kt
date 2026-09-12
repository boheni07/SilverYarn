package com.silveryarn.mobile.benchmark

import android.app.ActivityManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.os.PowerManager

/**
 * 벤치마크 하니스가 매 턴 끝에 찍는 기기 상태 스냅샷 3종 — `docs/03-check/
 * ondevice-slm-benchmark-protocol.md` §3의 측정 항목과 1:1 대응.
 *
 * 이 클래스 자체는 Android 프레임워크 API만 얇게 감싼 것이라 별도 유닛테스트를
 * 두지 않는다(테스트는 [percentile]·[SessionSummary]처럼 순수 로직만) — 실제
 * 정확성은 실기기에서 [android.os.Debug]/`dumpsys battery`와 값을 대조해 확인한다
 * (프로토콜 문서 §5 "측정값 검증" 참조).
 */
class DeviceProfiler(private val context: Context) {
    private val activityManager
        get() = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager

    private val powerManager
        get() = context.getSystemService(Context.POWER_SERVICE) as PowerManager

    /** 현재 프로세스의 PSS(Proportional Set Size) 기준 메모리 사용량(MB) — decisions.md
     * #31의 "~850MB" 목표치와 같은 단위로 맞췄다. `Debug.MemoryInfo.getTotalPss()`는 KB 단위. */
    fun snapshotMemoryMb(): Long {
        val pid = android.os.Process.myPid()
        val memoryInfo = activityManager.getProcessMemoryInfo(intArrayOf(pid)).firstOrNull() ?: return 0L
        return memoryInfo.totalPss / 1024L
    }

    /** 배터리 잔량 %(0~100). 짧은 세션(턴 몇 개)에서는 정수 % 특성상 변화가 안 잡힐
     * 수 있다 — 그 경우 프로토콜 문서가 요구하는 "장시간(1시간+) 반복 세션"으로 재측정. */
    fun snapshotBatteryPercent(): Int {
        val filter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        val batteryStatus: Intent? = context.registerReceiver(null, filter)
        val level = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        if (level < 0 || scale <= 0) return -1
        return (level * 100) / scale
    }

    /** `PowerManager.THERMAL_STATUS_*` 상수 그대로 반환(0=NONE ~ 6=SHUTDOWN). API 29
     * 미만(저사양 후보 기종이 걸릴 수 있는 Android 8~9)에서는 API 자체가 없어 -1(미지원)을
     * 반환 — 프로토콜 문서가 그 경우 기기 표면 온도 실측(적외선 온도계 등)으로 대체하도록
     * 안내한다. */
    fun snapshotThermalStatus(): Int {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return -1
        return powerManager.currentThermalStatus
    }
}
