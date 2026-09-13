package com.silveryarn.mobile.ondevice.slm

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/**
 * [SlmEngine]의 임시 구현체 — [com.silveryarn.mobile.ondevice.stt.MockSttEngine]과 짝을
 * 이루는 "가짜 응답" 엔진(실 모델 미선정, decisions.md #27). `userQuery`의 키워드를 얕게
 * 매칭해 그럴듯한 문장 2개를 decisions.md #31 "문장 단위 스트리밍"을 흉내 내 순차
 * emit한다 — 문장 사이 지연은 실제 추론 지연을 재현하려는 것이 아니라(실기기 벤치마크(#27)
 * 전에는 알 수 없다) 문장 단위로 말풍선이 늘어나며 TTS가 뒤따라 재생되는 파이프라이닝
 * UI를 이 스텁만으로도 눈에 보이게 하기 위함이다.
 *
 * **먼저 기억을 꺼내 묻기(사용자 요청)**: 매 3턴째마다 [PROACTIVE_FOLLOWUPS]를 순환하며
 * 세 번째 문장을 덧붙인다 — 사진("사진")·자서전 기록("자서전")·일정 알림 세 종류를
 * 순서대로 돌려, 은실이가 매번 사용자의 말만 되받는 게 아니라 먼저 화제를 꺼내는
 * 것처럼 보이게 한다. 문장에 포함된 "사진"/"자서전" 키워드는
 * [com.silveryarn.mobile.presentation.companion.ConversationSessionController]가 그대로
 * 다시 읽어 사진 카드 표시·`author` 모드 기록 여부를 결정하는 신호로 재사용한다(둘 다
 * 얕은 문자열 매칭 — 실 의도분류기가 붙기 전까지의 임시 규칙).
 *
 * `MockSttEngine`과 마찬가지로 실 SLM이 붙으면 이 파일만 지우고 [SlmEngine] 구현체로
 * 교체하면 된다.
 */
class MockSlmEngine : SlmEngine {
    private var turnCount = 0

    override fun generateStreamed(
        userQuery: String,
        context: String,
    ): Flow<String> =
        flow {
            val sentences = pickResponse(userQuery).toMutableList()
            if (turnCount % PROACTIVE_EVERY_N_TURNS == PROACTIVE_EVERY_N_TURNS - 1) {
                sentences.add(PROACTIVE_FOLLOWUPS[(turnCount / PROACTIVE_EVERY_N_TURNS) % PROACTIVE_FOLLOWUPS.size])
            }
            turnCount++
            for (sentence in sentences) {
                delay(SENTENCE_DELAY_MS)
                emit(sentence)
            }
        }

    private fun pickResponse(userQuery: String): List<String> =
        when {
            "날씨" in userQuery -> listOf("오늘 같은 날은 산책하기 참 좋겠어요.", "따뜻하게 입고 나가시는 거 잊지 마세요.")
            "잠" in userQuery -> listOf("잠이 잘 안 오시면 힘드시겠어요.", "낮에 잠깐 햇볕을 쬐시는 것도 도움이 된대요.")
            "무릎" in userQuery || "아프" in userQuery -> listOf("많이 불편하시겠어요.", "너무 무리하지 마시고 편히 쉬세요.")
            "손주" in userQuery || "손자" in userQuery || "손녀" in userQuery ->
                listOf("손주 이야기 하시니 얼굴이 환해지시네요.", "또 놀러 오면 좋겠어요.")
            else -> listOf("그러셨군요.", "오늘 하루는 어떠셨어요?")
        }

    companion object {
        private const val SENTENCE_DELAY_MS = 400L
        private const val PROACTIVE_EVERY_N_TURNS = 3
        private val PROACTIVE_FOLLOWUPS =
            listOf(
                "참, 지난번에 올려주신 사진 이야기를 좀 더 들려주실래요?",
                "오늘 이야기는 자서전에 넣어드릴게요.",
                "참, 오늘 오후에 병원 예약이 있으신 거 잊지 마세요.",
            )
    }
}
