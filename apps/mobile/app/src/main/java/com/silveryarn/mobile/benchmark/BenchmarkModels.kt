package com.silveryarn.mobile.benchmark

/**
 * 온디바이스 SLM 실기기 벤치마크(decisions.md #27, #31) 측정값 — 한 "대화 턴"
 * (구술 오디오 1건 → STT → SLM 첫 문장 → TTS 첫 오디오)의 결과.
 *
 * 지연시간 3종을 나눠 재는 이유는 decisions.md #31 "문장 단위 SLM 스트리밍→TTS
 * 파이프라이닝" 때문 — 사용자가 체감하는 응답성은 "SLM이 답을 다 만들 때까지"가
 * 아니라 "첫 문장이 TTS로 나오기까지"([ttsFirstAudioLatencyMs])가 기준이다.
 */
data class TurnMetrics(
    val turnIndex: Int,
    /** VAD가 발화 종료를 판정한 시점 → STT 텍스트 확보까지. */
    val sttLatencyMs: Long,
    /** STT 완료 → SLM이 첫 토큰(또는 첫 문장 경계)을 내보내기까지. */
    val slmFirstTokenLatencyMs: Long,
    /** STT 완료 → SLM 스트림이 끝까지 완료되기까지(참고용 — 사용자 체감 지표는 아님). */
    val slmTotalLatencyMs: Long,
    /** SLM 첫 문장 확보 → TTS가 그 문장의 오디오 재생을 시작하기까지. */
    val ttsFirstAudioLatencyMs: Long,
    /** VAD 종료 → TTS 첫 오디오 시작까지 — decisions.md #31의 목표치(0.8~1.2s)와
     * 직접 비교하는 사용자 체감 총 지연시간. */
    val totalTurnLatencyMs: Long,
    /** [DeviceProfiler.snapshotMemoryMb] — 이 턴이 끝난 시점의 프로세스 메모리(MB). */
    val memoryUsedMb: Long,
    /** [DeviceProfiler.snapshotBatteryPercent] — 이 턴이 끝난 시점의 배터리 잔량(%). */
    val batteryLevelPercent: Int,
    /** [DeviceProfiler.snapshotThermalStatus] — `PowerManager` 상수값 그대로(THERMAL_STATUS_*). */
    val thermalStatus: Int,
)

/**
 * 한 기기 × 한 SLM 후보 조합의 전체 세션 결과 — `docs/03-check/ondevice-slm-benchmark-protocol.md`의
 * 판정 기준과 이 값을 직접 대조한다.
 */
data class SessionSummary(
    val deviceModel: String,
    val slmCandidate: String,
    val turns: List<TurnMetrics>,
) {
    /** 배터리 잔량이 정수 %라 세션이 짧으면 0으로 나올 수 있다 — 그 경우 별도 장시간
     * 측정(mAh 단위)이 필요하다는 신호로 프로토콜 문서 §4에 명시. */
    val batteryDrainPercent: Int
        get() = (turns.firstOrNull()?.batteryLevelPercent ?: 0) - (turns.lastOrNull()?.batteryLevelPercent ?: 0)

    val peakMemoryMb: Long
        get() = turns.maxOfOrNull { it.memoryUsedMb } ?: 0L

    /** `PowerManager.THERMAL_STATUS_MODERATE`(2) 이상이 한 번이라도 나오면 조절(throttling)
     * 위험 신호로 본다 — 값 자체는 android.os.PowerManager 상수와 동일(여기선 Android 의존을
     * 피하려 정수로만 다룬다). */
    val thermalThrottled: Boolean
        get() = turns.any { it.thermalStatus >= THERMAL_STATUS_MODERATE_THRESHOLD }

    val totalLatencyP50Ms: Long
        get() = percentile(turns.map { it.totalTurnLatencyMs }, 0.50)

    val totalLatencyP95Ms: Long
        get() = percentile(turns.map { it.totalTurnLatencyMs }, 0.95)

    companion object {
        /** `android.os.PowerManager.THERMAL_STATUS_MODERATE` — 하니스가 Android 프레임워크에
         * 의존하지 않고도(순수 Kotlin, JVM 유닛테스트 가능) 판정할 수 있도록 상수를 복제해 둔다. */
        const val THERMAL_STATUS_MODERATE_THRESHOLD = 2
    }
}

/** 최근접 순위(nearest-rank) 백분위수 — 표본이 적은 벤치마크 세션(턴 수 십 단위)엔
 * 선형보간보다 이 방식이 이해하기 쉽고, decisions.md #31 목표치도 "약 얼마" 수준이라
 * 정밀 보간이 필요하지 않다. */
internal fun percentile(
    values: List<Long>,
    fraction: Double,
): Long {
    if (values.isEmpty()) return 0L
    val sorted = values.sorted()
    val index = (fraction * (sorted.size - 1)).toInt().coerceIn(0, sorted.size - 1)
    return sorted[index]
}
