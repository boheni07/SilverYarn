package com.silveryarn.mobile.ondevice.tts

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import kotlinx.coroutines.suspendCancellableCoroutine
import java.util.Locale
import java.util.UUID
import kotlin.coroutines.Continuation
import kotlin.coroutines.resume

/**
 * CONVENTIONS.md §2.2.1 "TTS: Android 네이티브 TTS" 후보의 구현체 — 추가 모델
 * 다운로드나 의존성 없이 OS 내장 TTS를 그대로 쓴다. 문장 단위 호출을 코루틴으로
 * 감싸 [SlmEngine.generateStreamed]가 내보내는 문장마다 순차 재생할 수 있게 했다.
 */
class AndroidNativeTtsEngine(
    context: Context,
) : TtsEngine {
    private var isReady = false

    // 발화(utteranceId)별 continuation — UtteranceProgressListener 콜백 하나를
    // 재사용하면서 speak()를 연달아 호출(QUEUE_ADD)해도 어떤 발화가 끝났는지 구분한다.
    private val pendingContinuations = HashMap<String, Continuation<Unit>>()

    private val utteranceListener =
        object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {}

            override fun onDone(utteranceId: String?) {
                pendingContinuations.remove(utteranceId)?.resume(Unit)
            }

            @Deprecated("Android SDK가 여전히 이 시그니처를 abstract로 요구해 구현만 해 둔다")
            override fun onError(utteranceId: String?) {
                pendingContinuations.remove(utteranceId)?.resume(Unit)
            }
        }

    // language 설정은 OnInitListener 콜백 안에서 해야 한다 — 생성자 직후엔 아직
    // 엔진 초기화(비동기)가 안 끝났을 수 있어 바로 이어서 설정하면 조용히 무시될 수 있다.
    private val tts: TextToSpeech =
        TextToSpeech(context.applicationContext) { status ->
            isReady = status == TextToSpeech.SUCCESS
            if (isReady) tts.language = Locale.KOREAN
        }

    init {
        tts.setOnUtteranceProgressListener(utteranceListener)
    }

    override suspend fun speakSentence(sentence: String) {
        if (!isReady) return
        val utteranceId = UUID.randomUUID().toString()
        suspendCancellableCoroutine<Unit> { continuation ->
            pendingContinuations[utteranceId] = continuation
            tts.speak(sentence, TextToSpeech.QUEUE_ADD, null, utteranceId)
        }
    }

    override fun stop() {
        tts.stop()
    }
}
