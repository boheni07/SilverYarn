package com.silveryarn.mobile.benchmark

import com.silveryarn.mobile.ondevice.slm.SlmEngine
import com.silveryarn.mobile.ondevice.stt.SttEngine
import com.silveryarn.mobile.ondevice.tts.TtsEngine
import kotlinx.coroutines.flow.collect

/** 하니스가 흘려보낼 대화 턴 1건 — 실제 기기 마이크 대신 미리 준비한 구술 오디오
 * 샘플을 쓴다(재현 가능한 비교를 위해, 프로토콜 문서 §2 "테스트 픽스처" 참조). */
data class BenchmarkTurn(
    val pcmAudio: ByteArray,
    /** FTS5 검색 + 최근 대화 이력으로 구성한 프롬프트 컨텍스트 — 실기기에서는
     * 실제 `autobiography_fts` 조회 결과를 넣는다. 하니스 자체는 이 문자열의
     * 출처를 모른다(호출자 책임). */
    val slmContext: String,
)

/**
 * STT → SLM → TTS를 순서대로 통과시키며 [TurnMetrics]를 재는 오케스트레이터 —
 * `docs/03-check/ondevice-slm-benchmark-protocol.md` §3 절차의 코드화.
 *
 * ⚠️ [SlmEngine]/[SttEngine]은 아직 실 구현체가 없다(decisions.md #27 — Kanana-2/
 * Qwen2.5-0.5B 등 후보만 있고 추론 런타임 연동 전). 이 클래스는 그 구현체가
 * 붙었을 때 곧바로 실행할 수 있는 측정 골격이다 — [UnimplementedSttEngine]/
 * [UnimplementedSlmEngine]을 그대로 넣고 돌리면 즉시 예외로 실패한다(의도적).
 *
 * [SlmEngine.generateStreamed]의 첫 스트림 조각을 "첫 문장"으로 간주해 시간을
 * 잰다 — 두 인터페이스의 문서 의도(decisions.md #31 "문장 단위 스트리밍→TTS
 * 파이프라이닝")를 그대로 따른 것이며, 실제 문장 경계 분리 로직은 이 하니스가
 * 아니라 프로덕션 오케스트레이터(아직 미구현)의 책임이다.
 */
class ConversationBenchmarkRunner(
    private val stt: SttEngine,
    private val slm: SlmEngine,
    private val tts: TtsEngine,
    private val profiler: DeviceProfiler,
) {
    suspend fun runSession(
        deviceModel: String,
        slmCandidate: String,
        turns: List<BenchmarkTurn>,
    ): SessionSummary {
        val results = turns.mapIndexed { index, turn -> runTurn(index, turn) }
        return SessionSummary(deviceModel = deviceModel, slmCandidate = slmCandidate, turns = results)
    }

    private suspend fun runTurn(
        index: Int,
        turn: BenchmarkTurn,
    ): TurnMetrics {
        val turnStart = System.nanoTime()

        val sttStart = System.nanoTime()
        val transcript = stt.transcribe(turn.pcmAudio)
        val sttLatencyMs = elapsedMs(sttStart)

        val slmStart = System.nanoTime()
        var firstSentence = ""
        var firstTokenAtNanos = slmStart
        var lastChunkAtNanos = slmStart
        var sawFirstChunk = false
        slm.generateStreamed(userQuery = transcript, context = turn.slmContext).collect { chunk ->
            if (!sawFirstChunk) {
                firstSentence = chunk
                firstTokenAtNanos = System.nanoTime()
                sawFirstChunk = true
            }
            lastChunkAtNanos = System.nanoTime()
        }
        val slmFirstTokenLatencyMs = (firstTokenAtNanos - slmStart).nanosToMs()
        // 참고용 — 사용자 체감 지표는 아니다(클래스 docstring 참조).
        val slmTotalLatencyMs = (lastChunkAtNanos - slmStart).nanosToMs()

        val ttsStart = System.nanoTime()
        tts.speakSentence(firstSentence)
        val ttsFirstAudioLatencyMs = elapsedMs(ttsStart)

        val totalTurnLatencyMs = elapsedMs(turnStart)

        return TurnMetrics(
            turnIndex = index,
            sttLatencyMs = sttLatencyMs,
            slmFirstTokenLatencyMs = slmFirstTokenLatencyMs,
            slmTotalLatencyMs = slmTotalLatencyMs,
            ttsFirstAudioLatencyMs = ttsFirstAudioLatencyMs,
            totalTurnLatencyMs = totalTurnLatencyMs,
            memoryUsedMb = profiler.snapshotMemoryMb(),
            batteryLevelPercent = profiler.snapshotBatteryPercent(),
            thermalStatus = profiler.snapshotThermalStatus(),
        )
    }

    private fun elapsedMs(startNanos: Long): Long = (System.nanoTime() - startNanos).nanosToMs()

    private fun Long.nanosToMs(): Long = this / 1_000_000L
}
