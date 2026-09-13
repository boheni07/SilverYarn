package com.silveryarn.mobile.presentation.care

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

/** 대화 턴 진행 단계 — [CareConversationScreen]이 이 값을 그대로 마이크 버튼/안내
 * 문구에 반영한다. `Speaking`은 SLM이 문장을 낼 때마다 지금까지 누적된 응답을
 * 들고 있어 화면이 "타이핑되듯" 늘어나는 말풍선을 그릴 수 있게 한다. */
sealed interface TurnPhase {
    data object Idle : TurnPhase

    data object Listening : TurnPhase

    data object Processing : TurnPhase

    data class Speaking(val partialResponse: String) : TurnPhase
}

/** 대화 로그 한 줄(사용자 발화 + AI 응답) — 화면 표시용. */
data class ConversationTurnUi(
    val turnId: Int,
    val userText: String,
    val assistantText: String,
)

/**
 * 말벗돌봄 모드(M4) 대화 턴 하나의 전체 처리 — STT(듣기) → SLM(생각하기, 문장 단위
 * 스트리밍) → TTS(말하기) → 로컬 DB 기록까지 실제 파이프라인 그대로 흘려보낸다.
 * `stt`/`slm`만 [com.silveryarn.mobile.ondevice.stt.MockSttEngine]/
 * [com.silveryarn.mobile.ondevice.slm.MockSlmEngine](decisions.md #27 모델 미선정)이고
 * 나머지 — Room 기록([ConversationDao]), TTS 재생, 이어지는
 * [com.silveryarn.mobile.sync.SyncWorker] 업로드 — 는 전부 실물이다.
 *
 * **더미 오디오 파일**: 실 마이크 캡처([android.media.AudioRecord])가 아직 없어(VAD도
 * 마찬가지, CONVENTIONS.md §2.2.1 확정 전) "듣기"는 고정 지연으로 흉내만 낸다. 다만
 * `conversations.audio_path`가 null이면 [com.silveryarn.mobile.sync.SyncRunner]가 그
 * 행을 업로드 대상에서 건너뛰므로([SyncRunner.runOnce] 참조), sync 파이프라인까지
 * 실물로 시연하려면 뭔가는 그 자리에 있어야 한다 — 그래서 내용 없는(무음) 더미
 * PCM 파일을 실제로 파일시스템에 써서 그 경로를 넘긴다. 이 파일의 바이트 자체는
 * 실 오디오가 아니라는 점을 명확히 하기 위해 이름에 `mock_` 접두사를 붙인다.
 */
class ConversationSessionController(
    private val context: Context,
    private val mode: String,
    private val stt: SttEngine,
    private val slm: SlmEngine,
    private val tts: TtsEngine,
) {
    private val sessionId: String = UUID.randomUUID().toString()
    private var nextTurnId = 0

    suspend fun runTurn(onPhaseChange: (TurnPhase) -> Unit): ConversationTurnUi {
        val turnStartMs = System.currentTimeMillis()
        val turnId = nextTurnId
        nextTurnId += 1

        onPhaseChange(TurnPhase.Listening)
        delay(LISTENING_DELAY_MS) // 실 VAD 800ms 묵음판정(decisions.md #32) 타이밍만 흉내
        val audioFile = writeMockAudioPlaceholder(turnId)

        onPhaseChange(TurnPhase.Processing)
        val userText = stt.transcribe(ByteArray(0))
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
        return ConversationTurnUi(turnId = turnId, userText = userText, assistantText = assistantText)
    }

    /** GET /sync/download가 받아 온 `persona_snapshot`(design.md §2.11 4단계) — 아직
     * 소비하는 곳이 없다고 [SyncRunner]에 적혀 있던 그 캐시를 여기서 처음 소비한다.
     * 값이 없으면(초기 상태) 빈 문자열 — [MockSlmEngine]은 어차피 얕은 키워드 매칭이라
     * 없어도 동작에 지장은 없다. */
    private suspend fun loadPersonaContext(): String {
        val deviceState = AppDatabase.getInstance(context).deviceStateDao().get()
        return deviceState?.personaSummary.orEmpty()
    }

    private fun writeMockAudioPlaceholder(turnId: Int): File {
        val dir = File(context.filesDir, "mock_audio").apply { mkdirs() }
        val file = File(dir, "mock_${sessionId}_$turnId.pcm")
        file.writeBytes(ByteArray(MOCK_AUDIO_BYTE_COUNT))
        return file
    }

    companion object {
        private const val LISTENING_DELAY_MS = 800L
        private const val MOCK_AUDIO_BYTE_COUNT = 64
    }
}
