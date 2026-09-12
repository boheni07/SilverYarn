package com.silveryarn.mobile.benchmark

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

private fun turn(
    index: Int,
    totalLatencyMs: Long,
    memoryMb: Long = 0L,
    batteryPercent: Int = 100,
    thermalStatus: Int = 0,
) = TurnMetrics(
    turnIndex = index,
    sttLatencyMs = 0,
    slmFirstTokenLatencyMs = 0,
    slmTotalLatencyMs = 0,
    ttsFirstAudioLatencyMs = 0,
    totalTurnLatencyMs = totalLatencyMs,
    memoryUsedMb = memoryMb,
    batteryLevelPercent = batteryPercent,
    thermalStatus = thermalStatus,
)

class PercentileTest {
    @Test
    fun `빈 목록이면 0`() {
        assertEquals(0L, percentile(emptyList(), 0.5))
    }

    @Test
    fun `p50은_정렬된_값의_중앙_근접값`() {
        val values = listOf(100L, 200L, 300L, 400L, 500L)
        assertEquals(300L, percentile(values, 0.5))
    }

    @Test
    fun `p95는_상위_근접값`() {
        val values = (1..20).map { it * 100L } // 100..2000
        assertEquals(1900L, percentile(values, 0.95))
    }

    @Test
    fun `정렬 안 된 입력도 정렬해서 계산`() {
        val values = listOf(500L, 100L, 300L)
        assertEquals(300L, percentile(values, 0.5))
    }
}

class SessionSummaryTest {
    @Test
    fun `배터리_소모는_첫_턴에서_마지막_턴을_뺀_값`() {
        val summary =
            SessionSummary(
                deviceModel = "Test-Device",
                slmCandidate = "kanana-2",
                turns = listOf(turn(0, 900, batteryPercent = 80), turn(1, 900, batteryPercent = 76)),
            )
        assertEquals(4, summary.batteryDrainPercent)
    }

    @Test
    fun `피크_메모리는_턴_중_최댓값`() {
        val summary =
            SessionSummary(
                deviceModel = "Test-Device",
                slmCandidate = "kanana-2",
                turns = listOf(turn(0, 900, memoryMb = 700), turn(1, 900, memoryMb = 850)),
            )
        assertEquals(850L, summary.peakMemoryMb)
    }

    @Test
    fun `열_조절_임계값_이상이_한_번이라도_있으면_throttled`() {
        val summary =
            SessionSummary(
                deviceModel = "Test-Device",
                slmCandidate = "kanana-2",
                turns = listOf(turn(0, 900, thermalStatus = 1), turn(1, 900, thermalStatus = 2)),
            )
        assertTrue(summary.thermalThrottled)
    }

    @Test
    fun `열_조절_임계값_미만만_있으면_throttled_아님`() {
        val summary =
            SessionSummary(
                deviceModel = "Test-Device",
                slmCandidate = "kanana-2",
                turns = listOf(turn(0, 900, thermalStatus = 0), turn(1, 900, thermalStatus = 1)),
            )
        assertFalse(summary.thermalThrottled)
    }

    @Test
    fun `턴이_없으면_모든_집계가_0`() {
        val summary = SessionSummary(deviceModel = "Test-Device", slmCandidate = "kanana-2", turns = emptyList())
        assertEquals(0L, summary.peakMemoryMb)
        assertEquals(0, summary.batteryDrainPercent)
        assertFalse(summary.thermalThrottled)
        assertEquals(0L, summary.totalLatencyP50Ms)
    }
}
