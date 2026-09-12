package com.silveryarn.mobile.benchmark

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CsvReportWriterTest {
    private val sampleTurn =
        TurnMetrics(
            turnIndex = 0,
            sttLatencyMs = 120,
            slmFirstTokenLatencyMs = 300,
            slmTotalLatencyMs = 900,
            ttsFirstAudioLatencyMs = 150,
            totalTurnLatencyMs = 570,
            memoryUsedMb = 780,
            batteryLevelPercent = 92,
            thermalStatus = 1,
        )
    private val sampleSummary =
        SessionSummary(deviceModel = "Galaxy-A35", slmCandidate = "qwen2.5-0.5b-4bit", turns = listOf(sampleTurn))

    @Test
    fun `상세_CSV는_헤더와_턴_수만큼의_행을_가진다`() {
        val csv = CsvReportWriter.toDetailCsv(sampleSummary)
        val lines = csv.trim().lines()
        assertEquals(2, lines.size) // 헤더 1 + 턴 1
        assertTrue(lines[0].startsWith("device_model,slm_candidate,turn_index"))
        assertTrue(lines[1].startsWith("Galaxy-A35,qwen2.5-0.5b-4bit,0,120,300,900,150,570,780,92,1"))
    }

    @Test
    fun `요약_라인은_기기_후보_턴수_지표_순서로_한_줄`() {
        val line = CsvReportWriter.toSummaryLine(sampleSummary)
        val fields = line.split(",")
        assertEquals("Galaxy-A35", fields[0])
        assertEquals("qwen2.5-0.5b-4bit", fields[1])
        assertEquals("1", fields[2]) // turn_count
    }

    @Test
    fun `턴이_없어도_헤더는_그대로_출력`() {
        val empty = SessionSummary(deviceModel = "Galaxy-S10", slmCandidate = "kanana-2-4bit", turns = emptyList())
        val csv = CsvReportWriter.toDetailCsv(empty)
        assertEquals(1, csv.trim().lines().size)
    }
}
