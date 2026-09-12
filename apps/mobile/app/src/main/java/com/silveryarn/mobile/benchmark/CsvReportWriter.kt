package com.silveryarn.mobile.benchmark

/**
 * [SessionSummary]를 스프레드시트로 바로 열 수 있는 CSV로 직렬화 — 여러 기기·후보
 * 조합의 결과를 한 표로 모아 비교하는 게 목적이라(프로토콜 문서 §6 "결과 취합"),
 * 매 세션 결과를 이 형식으로 남기면 그대로 이어붙일 수 있다.
 *
 * Android 프레임워크에 의존하지 않는 순수 함수라 JVM 유닛테스트로 검증한다.
 */
object CsvReportWriter {
    private const val HEADER =
        "device_model,slm_candidate,turn_index,stt_latency_ms,slm_first_token_latency_ms," +
            "slm_total_latency_ms,tts_first_audio_latency_ms,total_turn_latency_ms," +
            "memory_used_mb,battery_level_percent,thermal_status"

    /** 턴별 상세 행 — 원자료를 보존해 나중에 다른 방식으로 재집계할 수 있게 한다. */
    fun toDetailCsv(summary: SessionSummary): String {
        val rows =
            summary.turns.joinToString("\n") { turn ->
                listOf(
                    summary.deviceModel,
                    summary.slmCandidate,
                    turn.turnIndex,
                    turn.sttLatencyMs,
                    turn.slmFirstTokenLatencyMs,
                    turn.slmTotalLatencyMs,
                    turn.ttsFirstAudioLatencyMs,
                    turn.totalTurnLatencyMs,
                    turn.memoryUsedMb,
                    turn.batteryLevelPercent,
                    turn.thermalStatus,
                ).joinToString(",")
            }
        return "$HEADER\n$rows"
    }

    /** 기기 × 후보 한 줄 요약 — 여러 세션을 이어붙여 비교표를 만들 때 쓴다. */
    fun toSummaryLine(summary: SessionSummary): String =
        listOf(
            summary.deviceModel,
            summary.slmCandidate,
            summary.turns.size,
            summary.totalLatencyP50Ms,
            summary.totalLatencyP95Ms,
            summary.peakMemoryMb,
            summary.batteryDrainPercent,
            summary.thermalThrottled,
        ).joinToString(",")

    const val SUMMARY_HEADER =
        "device_model,slm_candidate,turn_count,total_latency_p50_ms,total_latency_p95_ms," +
            "peak_memory_mb,battery_drain_percent,thermal_throttled"
}
