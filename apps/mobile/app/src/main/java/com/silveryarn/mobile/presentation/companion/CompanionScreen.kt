package com.silveryarn.mobile.presentation.companion

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.silveryarn.mobile.local.db.UnrecalledPhotoEntity
import com.silveryarn.mobile.ondevice.slm.MockSlmEngine
import com.silveryarn.mobile.ondevice.stt.MockSttEngine
import com.silveryarn.mobile.ondevice.tts.AndroidNativeTtsEngine
import com.silveryarn.mobile.ondevice.vad.AmplitudeVoiceActivityDetector
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

// 브랜드 컬러(design-tokens.md) 직접 사용 — 앱 전역 MaterialTheme 커스터마이즈는 아직
// 미착수라(MainActivity.kt 참조), 은실이의 정체성을 드러내는 아바타·말풍선 색에 한해
// 최소로 하드코딩한다.
private val CompanionTeal = Color(0xFF1E7A8C)
private val CompanionTealDeep = Color(0xFF155C6B)
private val CompanionTealTint = Color(0xFFE4F0F2)
private val CompanionGold = Color(0xFFB8935A)
private val CompanionGoldDeep = Color(0xFF96723F)
private val CompanionGoldTint = Color(0xFFF3E9D8)

/**
 * 은실이 — 어르신 전용 대화형 홈 화면(사용자 요청, 2026-09-13 "모든 조작은 대화로").
 * 하단 4탭(대화/자서전/일정/설정, PR #23)을 걷어내고 이 화면 하나로 통합했다 — 자서전
 * 작가모드·비서모드가 하던 일(회고 질문, 일정 안내)도 은실이가 대화 중에 자연스럽게
 * 먼저 꺼낸다(design.md §2.10 페르소나 통일, [MockSlmEngine]의 "먼저 기억을 꺼내 묻기"
 * 참조). 설정은 일반 모드용 아주 작은 진입점만 [com.silveryarn.mobile.presentation.AppShell]에
 * 남아있다 — 키오스크 모드는 원래도 설정 접근 자체가 잠겨 있었다(decisions.md #6).
 *
 * **말하기 시작 두 가지 경로**(사용자 요청): ① 버튼을 눌러 시작 — 진폭 임계값을 기다리지
 * 않고 즉시 발화 중으로 간주한다. ② 그냥 말을 걸기 — [AmplitudeVoiceActivityDetector]가
 * 진폭이 임계값을 넘는 순간을 스스로 감지해 같은 파이프라인을 탄다. 두 경로 모두 종료
 * 판정(무음 800ms)과 이후 처리는 완전히 동일하다.
 *
 * 마이크 권한이 없으면(거부·아직 미승인) 자동감지 경로만 못 쓰고, 버튼 경로는 고정
 * 지연(800ms)으로 흉내 내는 대체 흐름으로 계속 동작한다([ConversationSessionController]
 * 참조) — 권한이 이 화면의 필수 전제조건은 아니다.
 */
@Composable
fun CompanionScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    val tts = remember { AndroidNativeTtsEngine(context) }
    val detector = remember { AmplitudeVoiceActivityDetector(context) }
    val session =
        remember {
            ConversationSessionController(
                context = context,
                stt = MockSttEngine(),
                slm = MockSlmEngine(),
                tts = tts,
            )
        }

    var phase by remember { mutableStateOf<TurnPhase>(TurnPhase.Idle) }
    var busy by remember { mutableStateOf(false) }
    var nextMessageId by remember { mutableStateOf(0) }
    var messages by remember { mutableStateOf(emptyList<ChatMessage>()) }
    var micGranted by
        remember {
            mutableStateOf(
                context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED,
            )
        }

    fun addMessage(
        speaker: Speaker,
        text: String,
        photo: UnrecalledPhotoEntity? = null,
        chapterSaved: Boolean = false,
    ) {
        messages = messages + ChatMessage(nextMessageId, speaker, text, photo, chapterSaved)
        nextMessageId += 1
    }

    val permissionLauncher =
        rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            micGranted = granted
            addMessage(
                Speaker.COMPANION,
                if (granted) {
                    "고마워요! 이제 그냥 편하게 말씀하시면 제가 알아들을게요."
                } else {
                    "괜찮아요, 그러면 아래 버튼을 눌러서 말씀해 주세요."
                },
            )
        }

    LaunchedEffect(Unit) {
        val stats = runCatching { loadCompanionStats(context) }.getOrNull()
        addMessage(Speaker.COMPANION, companionGreeting(stats))
        if (!micGranted) {
            addMessage(Speaker.COMPANION, "마이크를 쓸 수 있게 허락해 주시면, 그냥 말씀만 하셔도 제가 알아들을 수 있어요.")
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    suspend fun runTurn(capturedAudio: ByteArray?) {
        if (busy) return
        busy = true
        detector.pause()
        val result = session.runTurn(capturedAudio) { newPhase -> phase = newPhase }
        addMessage(Speaker.USER, result.userText)
        addMessage(
            Speaker.COMPANION,
            result.assistantText,
            photo = result.photo,
            chapterSaved = result.mode == "author",
        )
        detector.resumeListening()
        busy = false
    }

    LaunchedEffect(micGranted) {
        if (micGranted) {
            detector.start(
                scope = this,
                onSpeechStarted = {
                    coroutineScope.launch(Dispatchers.Main) {
                        if (phase == TurnPhase.Idle) phase = TurnPhase.Listening
                    }
                },
                onUtteranceCaptured = { pcm ->
                    coroutineScope.launch(Dispatchers.Main) { runTurn(pcm) }
                },
            )
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            detector.stop()
            tts.stop()
        }
    }

    Column(
        modifier = modifier.fillMaxSize().padding(horizontal = 20.dp, vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CompanionAvatar(phase = phase)
        Spacer(Modifier.height(6.dp))
        Text("은실이", style = MaterialTheme.typography.titleMedium)
        Text(phaseCaption(phase), style = MaterialTheme.typography.labelMedium)

        Spacer(Modifier.height(14.dp))

        ConversationThread(messages = messages, phase = phase, modifier = Modifier.weight(1f).fillMaxWidth())

        Spacer(Modifier.height(14.dp))

        Button(
            onClick = {
                if (phase == TurnPhase.Idle && !busy) {
                    if (micGranted) {
                        detector.triggerManualStart()
                    } else {
                        coroutineScope.launch { runTurn(null) }
                    }
                }
            },
            enabled = phase == TurnPhase.Idle && !busy,
            modifier = Modifier.size(96.dp),
            shape = CircleShape,
        ) {
            Text("🎙", style = MaterialTheme.typography.headlineMedium)
        }
    }
}

@Composable
private fun CompanionAvatar(phase: TurnPhase) {
    val active = phase != TurnPhase.Idle
    val transition = rememberInfiniteTransition(label = "companion-pulse")
    val pulse by
        transition.animateFloat(
            initialValue = 0f,
            targetValue = 1f,
            animationSpec =
                infiniteRepeatable(animation = tween(1100, easing = LinearEasing), repeatMode = RepeatMode.Restart),
            label = "pulse",
        )
    val ringColor =
        when (phase) {
            TurnPhase.Idle -> Color.Transparent
            TurnPhase.Listening -> CompanionTeal
            TurnPhase.Processing -> CompanionGold
            is TurnPhase.Speaking -> CompanionGoldDeep
        }

    Box(contentAlignment = Alignment.Center) {
        if (active) {
            Box(
                modifier =
                    Modifier
                        .size(64.dp + (26.dp * pulse))
                        .alpha(1f - pulse)
                        .border(width = 2.dp, color = ringColor, shape = CircleShape),
            )
        }
        Box(
            modifier =
                Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(Brush.sweepGradient(listOf(CompanionTeal, CompanionGold, CompanionTeal))),
            contentAlignment = Alignment.Center,
        ) {
            Text("🧶", fontSize = 26.sp)
        }
    }
}

private fun phaseCaption(phase: TurnPhase): String =
    when (phase) {
        TurnPhase.Idle -> "편하게 말씀해 보세요"
        TurnPhase.Listening -> "듣고 있어요…"
        TurnPhase.Processing -> "생각하고 있어요…"
        is TurnPhase.Speaking -> "말하고 있어요…"
    }

@Composable
private fun ConversationThread(
    messages: List<ChatMessage>,
    phase: TurnPhase,
    modifier: Modifier = Modifier,
) {
    LazyColumn(modifier = modifier, verticalArrangement = Arrangement.spacedBy(10.dp)) {
        items(messages, key = { it.id }) { message -> ChatBubble(message) }

        val speaking = phase as? TurnPhase.Speaking
        if (speaking != null) {
            item {
                ChatBubble(ChatMessage(id = -1, speaker = Speaker.COMPANION, text = speaking.partialResponse))
            }
        }
    }
}

@Composable
private fun ChatBubble(message: ChatMessage) {
    val isUser = message.speaker == Speaker.USER
    val arrangement = if (isUser) Arrangement.End else Arrangement.Start
    val bubbleColor = if (isUser) CompanionTealTint else CompanionGoldTint
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = arrangement) {
        Column(horizontalAlignment = if (isUser) Alignment.End else Alignment.Start) {
            Card(colors = CardDefaults.cardColors(containerColor = bubbleColor)) {
                Text(message.text, modifier = Modifier.padding(12.dp))
            }
            if (message.photo != null) PhotoHintCard(message.photo)
            if (message.chapterSaved) ChapterSavedChip()
        }
    }
}

/** "사진" 언급 턴이고 [ConversationSessionController]가 실제 로컬 미회고 사진 캐시
 * (`unrecalled_photos`)에서 항목을 찾았을 때만 그려진다 — 캐시가 비어 있으면 가짜
 * 사진 정보를 지어내지 않고 그냥 표시하지 않는다. */
@Composable
private fun PhotoHintCard(photo: UnrecalledPhotoEntity) {
    Card(modifier = Modifier.padding(top = 6.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(10.dp)) {
            Text("🖼", fontSize = 20.sp)
            Spacer(Modifier.width(8.dp))
            Column {
                Text(photo.caption ?: "사진", style = MaterialTheme.typography.labelMedium)
                photo.yearTag?.let { Text("${it}년", style = MaterialTheme.typography.labelSmall) }
            }
        }
    }
}

@Composable
private fun ChapterSavedChip() {
    Card(
        modifier = Modifier.padding(top = 6.dp),
        colors = CardDefaults.cardColors(containerColor = CompanionTealTint),
    ) {
        Text(
            "📖 자서전에 저장됨",
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            style = MaterialTheme.typography.labelMedium,
            color = CompanionTealDeep,
        )
    }
}
