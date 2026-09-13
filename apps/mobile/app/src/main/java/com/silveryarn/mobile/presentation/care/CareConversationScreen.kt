package com.silveryarn.mobile.presentation.care

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.silveryarn.mobile.ondevice.slm.MockSlmEngine
import com.silveryarn.mobile.ondevice.stt.MockSttEngine
import com.silveryarn.mobile.ondevice.tts.AndroidNativeTtsEngine
import kotlinx.coroutines.launch

/**
 * 말벗돌봄 모드(M4) 대화 화면 — [com.silveryarn.mobile.presentation.AppShell]이 "대화" 탭에서
 * 마이크를 탭하면 진입시킨다.
 *
 * STT/SLM은 아직 [MockSttEngine]/[MockSlmEngine](decisions.md #27 최종 모델 미선정)이고,
 * 그 외 흐름 — 세션·턴 진행, Room DB 기록, TTS 재생, 뒤이은
 * [com.silveryarn.mobile.sync.SyncWorker] 업로드 — 은 [ConversationSessionController]가
 * 실물 그대로 처리한다. 실 모델이 준비되면 이 화면은 그대로 두고 두 Mock 엔진 생성부만
 * 교체하면 된다.
 */
@Composable
fun CareConversationScreen(
    modifier: Modifier = Modifier,
    onEndSession: () -> Unit = {},
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val tts = remember { AndroidNativeTtsEngine(context) }
    val session =
        remember {
            ConversationSessionController(
                context = context,
                mode = "care",
                stt = MockSttEngine(),
                slm = MockSlmEngine(),
                tts = tts,
            )
        }

    var phase by remember { mutableStateOf<TurnPhase>(TurnPhase.Idle) }
    var turns by remember { mutableStateOf(emptyList<ConversationTurnUi>()) }

    // 화면을 벗어나면(탭 전환 등) 재생 중이던 TTS를 멈춘다 — [AndroidNativeTtsEngine]엔
    // 완전한 해제(shutdown)가 없어 stop()까지만(현재 인터페이스가 지원하는 전부).
    DisposableEffect(Unit) {
        onDispose { tts.stop() }
    }

    Column(modifier = modifier.fillMaxSize().padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("말벗돌봄 모드", style = MaterialTheme.typography.titleMedium)
            TextButton(onClick = onEndSession) { Text("종료") }
        }

        Spacer(Modifier.height(8.dp))

        ConversationLog(
            turns = turns,
            phase = phase,
            modifier = Modifier.weight(1f).fillMaxWidth(),
        )

        Spacer(Modifier.height(8.dp))

        PhaseCaption(phase)

        Button(
            onClick = {
                if (phase == TurnPhase.Idle) {
                    coroutineScope.launch {
                        val turn = session.runTurn { newPhase -> phase = newPhase }
                        turns = turns + turn
                    }
                }
            },
            enabled = phase == TurnPhase.Idle,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(if (phase == TurnPhase.Idle) "🎙 말씀해 주세요" else "…")
        }
    }
}

/** 지금까지의 대화 로그 — [phase]가 [TurnPhase.Speaking]인 동안엔 아직 저장 전인 진행 중
 * 응답도 마지막 줄에 같이 그려 스트리밍처럼 보이게 한다. */
@Composable
private fun ConversationLog(
    turns: List<ConversationTurnUi>,
    phase: TurnPhase,
    modifier: Modifier = Modifier,
) {
    LazyColumn(modifier = modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(turns) { turn ->
            ConversationBubblePair(userText = turn.userText, assistantText = turn.assistantText)
        }

        val speaking = phase as? TurnPhase.Speaking
        if (speaking != null) {
            item { ConversationBubblePair(userText = null, assistantText = speaking.partialResponse) }
        }
    }
}

@Composable
private fun ConversationBubblePair(
    userText: String?,
    assistantText: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        if (userText != null) {
            ConversationBubble(text = userText, alignment = Alignment.End)
        }
        ConversationBubble(text = assistantText, alignment = Alignment.Start)
    }
}

@Composable
private fun ConversationBubble(
    text: String,
    alignment: Alignment.Horizontal,
) {
    val arrangement = if (alignment == Alignment.End) Arrangement.End else Arrangement.Start
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = arrangement) {
        Card { Text(text, modifier = Modifier.padding(12.dp)) }
    }
}

@Composable
private fun PhaseCaption(phase: TurnPhase) {
    val label =
        when (phase) {
            TurnPhase.Idle -> null
            TurnPhase.Listening -> "듣고 있어요…"
            TurnPhase.Processing -> "생각하고 있어요…"
            is TurnPhase.Speaking -> "말하고 있어요…"
        }
    if (label != null) {
        Text(label, style = MaterialTheme.typography.labelMedium)
    }
}
