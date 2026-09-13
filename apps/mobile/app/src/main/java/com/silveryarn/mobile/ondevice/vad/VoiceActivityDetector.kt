package com.silveryarn.mobile.ondevice.vad

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sqrt

/**
 * 발화 시작·종료 판정 계약 — CONVENTIONS.md §2.2.1 "WebRTC VAD(800ms 묵음판정)" 후보가
 * 아직 실기기 벤치마크 전(decisions.md #27/#9/#31)이라, [AmplitudeVoiceActivityDetector]가
 * 그 자리를 채우는 진폭(RMS) 임계값 기반 임시 구현체다 — 판정 타이밍(무음 800ms)만은
 * 이미 결정된 값(decisions.md #32)을 그대로 따르고, 라이브러리 자체는 벤치마크 후 교체.
 */
interface VoiceActivityDetector {
    /** 무음 대기 상태로 마이크를 계속 듣다가, 진폭이 임계값을 넘으면 [onSpeechStarted]로
     * 실시간 알리고, 이후 무음이 [SILENCE_HOLD_MS] 이상 이어지면 그 구간 전체(사전
     * 녹음분 포함)를 [onUtteranceCaptured]로 넘긴다. [scope]가 취소되면 함께 멈춘다. */
    fun start(
        scope: CoroutineScope,
        onSpeechStarted: () -> Unit,
        onUtteranceCaptured: (ByteArray) -> Unit,
    )

    fun stop()

    /** 진폭 임계값을 기다리지 않고 이번 사이클을 즉시 발화 중으로 간주한다 —
     * "말하기" 버튼을 눌렀을 때 호출한다. 종료 판정(무음 800ms)은 자동 감지 경로와
     * 동일하게 공유하므로, 버튼으로 시작하든 그냥 말을 걸든 같은 파이프라인을 탄다. */
    fun triggerManualStart()

    /** TTS로 은실이가 말하는 동안 자기 목소리를 다시 듣지 않도록 판정을 잠시 멈춘다. */
    fun pause()

    fun resumeListening()
}

/**
 * [AudioRecord] 진폭(RMS)만으로 발화 시작/종료를 판정하는 임시 VAD 구현체.
 * 발화 시작 직전 [PRE_ROLL_CHUNKS]개 청크(~300ms)를 항상 들고 있다가 발화가 감지되면
 * 그 사전 녹음분부터 붙여 보내 — 임계값을 막 넘긴 시점의 첫 음절이 잘리지 않게 한다.
 */
class AmplitudeVoiceActivityDetector(
    private val context: Context,
) : VoiceActivityDetector {
    private var job: Job? = null
    private var manualTriggerRequested = false
    private var listeningEnabled = true

    override fun start(
        scope: CoroutineScope,
        onSpeechStarted: () -> Unit,
        onUtteranceCaptured: (ByteArray) -> Unit,
    ) {
        if (job?.isActive == true) return
        val granted = context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
        if (!granted) return
        job = scope.launch(Dispatchers.Default) { recordLoop(onSpeechStarted, onUtteranceCaptured) }
    }

    override fun stop() {
        job?.cancel()
        job = null
    }

    override fun triggerManualStart() {
        manualTriggerRequested = true
    }

    override fun pause() {
        listeningEnabled = false
    }

    override fun resumeListening() {
        listeningEnabled = true
    }

    private suspend fun CoroutineScope.recordLoop(
        onSpeechStarted: () -> Unit,
        onUtteranceCaptured: (ByteArray) -> Unit,
    ) {
        val minBuffer =
            AudioRecord.getMinBufferSize(SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        if (minBuffer <= 0) return
        val audioRecord =
            AudioRecord(
                MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                minBuffer * 2,
            )
        if (audioRecord.state != AudioRecord.STATE_INITIALIZED) {
            audioRecord.release()
            return
        }

        val chunk = ShortArray(CHUNK_SAMPLES)
        val preRoll = ArrayDeque<ShortArray>()
        val captured = mutableListOf<Short>()
        var speaking = false
        var silenceMs = 0L

        try {
            audioRecord.startRecording()
            while (isActive) {
                val read = audioRecord.read(chunk, 0, chunk.size)
                if (read <= 0) continue
                if (!listeningEnabled) {
                    speaking = false
                    preRoll.clear()
                    continue
                }

                val loud = rms(chunk, read) > SPEECH_RMS_THRESHOLD || manualTriggerRequested

                if (!speaking) {
                    preRoll.addLast(chunk.copyOf(read))
                    if (preRoll.size > PRE_ROLL_CHUNKS) preRoll.removeFirst()
                    if (loud) {
                        speaking = true
                        manualTriggerRequested = false
                        silenceMs = 0L
                        captured.clear()
                        preRoll.forEach { pre -> captured.addAll(pre.toList()) }
                        onSpeechStarted()
                    }
                } else {
                    for (index in 0 until read) captured.add(chunk[index])
                    if (rms(chunk, read) > SPEECH_RMS_THRESHOLD) {
                        silenceMs = 0L
                    } else {
                        silenceMs += CHUNK_MS
                        if (silenceMs >= SILENCE_HOLD_MS) {
                            speaking = false
                            onUtteranceCaptured(toPcmBytes(captured))
                        }
                    }
                }
            }
        } catch (unused: Exception) {
            // 마이크 접근 실패(권한 철회, 다른 앱 점유 등) — 수동 버튼 경로(권한 없을 때의
            // 대체 흐름, ConversationSessionController 참조)로 계속 쓸 수 있으니 조용히 종료.
        } finally {
            runCatching { audioRecord.stop() }
            runCatching { audioRecord.release() }
        }
    }

    private fun rms(
        chunk: ShortArray,
        length: Int,
    ): Double {
        var sumSquares = 0.0
        for (index in 0 until length) {
            val sample = chunk[index].toDouble()
            sumSquares += sample * sample
        }
        return sqrt(sumSquares / length)
    }

    private fun toPcmBytes(samples: List<Short>): ByteArray {
        val buffer = ByteBuffer.allocate(samples.size * 2).order(ByteOrder.LITTLE_ENDIAN)
        samples.forEach { buffer.putShort(it) }
        return buffer.array()
    }

    companion object {
        private const val SAMPLE_RATE = 16_000
        private const val CHUNK_MS = 20L
        private const val CHUNK_SAMPLES = 320 // SAMPLE_RATE(16_000) * CHUNK_MS(20) / 1000
        private const val PRE_ROLL_CHUNKS = 15 // ~300ms
        private const val SILENCE_HOLD_MS = 800L // decisions.md #32 "800ms 묵음판정"과 동일 기준

        // 실기기 벤치마크(#27/#9/#31) 전까지의 임시값 — 주변 소음 대비 발화 진폭 추정치.
        private const val SPEECH_RMS_THRESHOLD = 1200.0
    }
}
