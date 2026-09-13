package com.silveryarn.mobile.presentation.companion

import com.silveryarn.mobile.local.db.UnrecalledPhotoEntity

/** 대화 턴 진행 단계 — [CompanionScreen]이 이 값을 그대로 아바타 애니메이션·안내
 * 문구에 반영한다. `Speaking`은 SLM이 문장을 낼 때마다 지금까지 누적된 응답을
 * 들고 있어 화면이 "타이핑되듯" 늘어나는 말풍선을 그릴 수 있게 한다. */
sealed interface TurnPhase {
    data object Idle : TurnPhase

    data object Listening : TurnPhase

    data object Processing : TurnPhase

    data class Speaking(val partialResponse: String) : TurnPhase
}

enum class Speaker { COMPANION, USER }

/** 대화 로그 한 줄 — 화면 표시용. 은실이가 먼저 거는 인사말처럼 사용자 발화 없이
 * 시작하는 메시지도 있어([Speaker.COMPANION] 단독), 턴(사용자+응답) 단위가 아니라
 * 메시지 단위 리스트로 관리한다. */
data class ChatMessage(
    val id: Int,
    val speaker: Speaker,
    val text: String,
    /** "사진" 언급 턴이고 실제 로컬 미회고 사진 캐시에 항목이 있을 때만 채워진다 —
     * 없으면 카드를 그리지 않는다(가짜 데이터를 지어내지 않는다). */
    val photo: UnrecalledPhotoEntity? = null,
    /** 이번 턴이 `author` 모드로 기록됐음을 화면에 알리는 표시(자서전에 저장됨 칩). */
    val chapterSaved: Boolean = false,
)

/** [ConversationSessionController.runTurn] 결과 — 화면이 이 값으로 사용자·은실이
 * 메시지 두 개를 새로 만들어 대화 로그에 붙인다. */
data class ConversationTurnResult(
    val userText: String,
    val assistantText: String,
    /** "care" | "author" — conversation_chunks.mode(schema.md §5)와 동일한 값. */
    val mode: String,
    val photo: UnrecalledPhotoEntity?,
)
