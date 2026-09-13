package com.silveryarn.mobile.presentation.companion

import android.content.Context
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.local.db.ConversationEntity
import com.silveryarn.mobile.ondevice.slm.SlmEngine
import com.silveryarn.mobile.ondevice.stt.SttEngine
import com.silveryarn.mobile.ondevice.tts.TtsEngine
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collect
import java.io.File
import java.util.UUID

/**
 * 대화 턴 하나의 전체 처리 — STT(듣기) → SLM(생각하기, 문장 단위 스트리밍) → TTS(말하기)
 * → 로컬 DB 기록까지 실제 파이프라인 그대로 흘려보낸다. `stt`/`slm`만
 * [com.silveryarn.mobile.ondevice.stt.MockSttEngine]/[com.silveryarn.mobile.ondevice.slm.MockSlmEngine]
 * (decisions.md #27 모델 미선정)이고 나머지 — Room 기록([ConversationDao]), TTS 재생,
 * 이어지는 [com.silveryarn.mobile.sync.SyncWorker] 업로드 — 는 전부 실물이다.
 *
 * 예전엔 자서전 작가모드/말벗돌봄 모드가 화면별로 나뉘어 있었지만(하단 탭, 제거됨 —
 * 사용자 요청 "모든 조작을 대화로"), 이제는 화면이 하나뿐이라 어느 모드로 이번 턴을
 * 기록할지도 이 클래스가 정한다: 은실이의 응답이 "자서전"을 언급하면 `author`, 그 외엔
 * `care`(conversation_chunks.mode, schema.md §5) — 실 의도분류기가 붙기 전까지의
 * 얕은 문자열 매칭 규칙이다.
 *
 * **오디오**: [capturedAudio]가 있으면(실 마이크 캡처 — [com.silveryarn.mobile.ondevice.vad.VoiceActivityDetector]가
 * 이미 무음판정까지 마친 뒤 건네준 PCM) 그 바이트를 그대로 STT·업로드에 쓴다. 마이크
 * 권한이 없어 `null`이면(대체 경로) "듣기"를 800ms 고정 지연으로 흉내 내고 무음 더미
 * 바이트를 대신 채운다 — `conversations.audio_path`가 null이면
 * [com.silveryarn.mobile.sync.SyncRunner]가 그 행을 업로드 대상에서 건너뛰므로
 * ([SyncRunner.runOnce] 참조) 어느 경로든 뭔가는 파일로 남겨야 한다.
 */
class ConversationSessionController(
    private val context: Context,
    private val stt: SttEngine,
    private val slm: SlmEngine,
    private val tts: TtsEngine,
) {
    private val sessionId: String = UUID.randomUUID().toString()
    private var nextTurnId = 0

    suspend fun runTurn(
        capturedAudio: ByteArray?,
        onPhaseChange: (TurnPhase) -> Unit,
    ): ConversationTurnResult {
        val turnStartMs = System.currentTimeMillis()
        val turnId = nextTurnId
        nextTurnId += 1

        val pcm: ByteArray
        if (capturedAudio != null) {
            // VAD가 실시간으로 이미 듣고 무음판정까지 끝낸 뒤라 추가 지연이 필요 없다 —
            // 화면은 onSpeechStarted 콜백에서 이미 Listening으로 전환해 둔 상태다.
            pcm = capturedAudio
        } else {
            onPhaseChange(TurnPhase.Listening)
            delay(LISTENING_DELAY_MS)
            pcm = ByteArray(0)
        }
        val audioFile = writeAudioFile(turnId, pcm)

        onPhaseChange(TurnPhase.Processing)
        val userText = stt.transcribe(pcm)
        val personaContext = loadPersonaContext()

        val responseBuilder = StringBuilder()
        slm.generateStreamed(userQuery = userText, context = personaContext).collect { sentence ->
            if (responseBuilder.isNotEmpty()) responseBuilder.append(" ")
            responseBuilder.append(sentence)
            onPhaseChange(TurnPhase.Speaking(responseBuilder.toString()))
            tts.speakSentence(sentence)
        }
        val assistantText = responseBuilder.toString()
        val latencyMs = (System.currentTimeMillis() - turnStartMs).toInt()

        val mode = if ("자서전" in assistantText) "author" else "care"
        val photo =
            if ("사진" in assistantText) {
                AppDatabase.getInstance(context).unrecalledPhotoDao().peekNext()
            } else {
                null
            }

        AppDatabase.getInstance(context).conversationDao().upsert(
            ConversationEntity(
                id = UUID.randomUUID().toString(),
                sessionId = sessionId,
                turnId = turnId,
                mode = mode,
                userQuery = userText,
                assistantResponse = assistantText,
                audioPath = audioFile.absolutePath,
                linkedChapterId = null,
                responseLatencyMs = latencyMs,
                syncStatus = "PENDING",
                createdAt = turnStartMs,
            ),
        )

        onPhaseChange(TurnPhase.Idle)
        return ConversationTurnResult(userText = userText, assistantText = assistantText, mode = mode, photo = photo)
    }

    /** GET /sync/download가 받아 온 `persona_snapshot`(design.md §2.11 4단계) 소비 —
     * 값이 없으면(초기 상태) 빈 문자열. [com.silveryarn.mobile.ondevice.slm.MockSlmEngine]은
     * 어차피 얕은 키워드 매칭이라 없어도 동작에 지장은 없다. */
    private suspend fun loadPersonaContext(): String {
        val deviceState = AppDatabase.getInstance(context).deviceStateDao().get()
        return deviceState?.personaSummary.orEmpty()
    }

    private fun writeAudioFile(
        turnId: Int,
        pcm: ByteArray,
    ): File {
        val dir = File(context.filesDir, "captured_audio").apply { mkdirs() }
        val prefix = if (pcm.isEmpty()) "silent" else "captured"
        val file = File(dir, "${prefix}_${sessionId}_$turnId.pcm")
        file.writeBytes(if (pcm.isEmpty()) ByteArray(SILENT_PLACEHOLDER_BYTE_COUNT) else pcm)
        return file
    }

    companion object {
        private const val LISTENING_DELAY_MS = 800L
        private const val SILENT_PLACEHOLDER_BYTE_COUNT = 64
    }
}
