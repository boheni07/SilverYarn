package com.silveryarn.mobile.ondevice.tts

/** 온디바이스 TTS 엔진 계약 — [AndroidNativeTtsEngine]이 유일한 구현체(CONVENTIONS.md
 * §2.2.1 "Android 네이티브 TTS" 후보를 그대로 구현, 추가 의존성 없음). */
interface TtsEngine {
    /** 문장 단위로 즉시 호출 — decisions.md #31 스트리밍 파이프라이닝 참조. */
    suspend fun speakSentence(sentence: String)

    fun stop()
}
