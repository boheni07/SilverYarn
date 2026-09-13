package com.silveryarn.mobile.ondevice.stt

/**
 * [SttEngine]의 임시 구현체 — 실 STT 모델이 아직 선정되지 않은 상태(decisions.md #27)에서
 * 대화 화면·세션·로컬 DB·동기화 흐름을 실물처럼 시연하기 위한 "가짜 응답" 엔진이다.
 *
 * `benchmark/PlaceholderEngines.kt`의 `UnimplementedSttEngine`과는 목적이 정반대다 —
 * 그쪽은 실 구현체 없이 벤치마크를 돌리면 곧바로 예외로 실패하게 만드는 안전장치이고,
 * 이 클래스는 절대 실패하지 않고 그럴듯한 고정 문장을 순환 반환한다. 실 STT가 붙으면
 * 이 파일만 지우고 [SttEngine] 구현체로 교체하면 된다 — 호출부
 * ([com.silveryarn.mobile.presentation.companion.ConversationSessionController])는 인터페이스만
 * 알아 변경이 필요 없다.
 *
 * `pcmAudio`는 내용을 보지 않는다 — 실 마이크 캡처([android.media.AudioRecord])가 아직
 * 없어 호출부가 항상 무음 더미 바이트를 넘긴다는 전제와도 무관하게, 이 스텁 자체가
 * 오디오 내용과 무관한 고정 응답이라는 뜻이다.
 */
class MockSttEngine : SttEngine {
    private var cursor = 0

    override suspend fun transcribe(pcmAudio: ByteArray): String {
        val text = SAMPLE_TRANSCRIPTS[cursor % SAMPLE_TRANSCRIPTS.size]
        cursor += 1
        return text
    }

    companion object {
        private val SAMPLE_TRANSCRIPTS =
            listOf(
                "오늘 날씨가 참 좋네요.",
                "점심으로 뭘 먹을지 고민이에요.",
                "요즘 밤에 잠이 잘 안 와요.",
                "어제 손주가 놀러 왔었어요.",
                "무릎이 좀 쑤시는 것 같아요.",
            )
    }
}
