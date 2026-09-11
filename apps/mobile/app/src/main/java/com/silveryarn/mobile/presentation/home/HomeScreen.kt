package com.silveryarn.mobile.presentation.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

/**
 * 홈 · 음성 대화 메인(M2, UI/UX 화면설계서) — 앱 실행 시 진입하는 기본 화면.
 *
 * 마이크를 탭하면 [onStartConversation]이 호출된다. 실제로는 온디바이스 SLM 라우터가
 * 발화 의도를 분류해 자서전 작가 모드(M3)·말벗돌봄 모드(M4)로 자동 라우팅해야 하지만
 * (workflow-diagrams.md §19), 그 라우터([com.silveryarn.mobile.ondevice.slm.SlmEngine])가
 * 아직 스텁이라 지금은 호출자([com.silveryarn.mobile.presentation.AppShell])가 고정된
 * 기본 목적지(말벗돌봄 모드)로 보낸다 — 라우터가 붙으면 이 화면은 그대로 두고
 * 호출자 쪽 분기만 교체하면 된다.
 */
@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    onStartConversation: () -> Unit = {},
) {
    val context = LocalContext.current
    var stats by remember { mutableStateOf<HomeStats?>(null) }

    LaunchedEffect(Unit) {
        stats = loadHomeStats(context)
    }

    Column(
        modifier =
            modifier
                .fillMaxSize()
                .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        val greeting = stats?.userName?.let { "안녕하세요, ${it}님" } ?: "안녕하세요"
        Text(greeting, style = MaterialTheme.typography.headlineSmall)

        MicButton(onClick = onStartConversation, modifier = Modifier.align(Alignment.CenterHorizontally))

        val question = stats?.nextQuestion
        if (question != null) {
            QuestionCard(question)
        }

        StatRow(stats)
    }
}

/** M2 요소 2 — 핵심 CTA. 무음 자동종료·길게 눌러 수동종료 등 실제 VAD 연동은
 * [com.silveryarn.mobile.ondevice.stt.SttEngine] 붙은 뒤 구현. */
@Composable
private fun MicButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Button(
        onClick = onClick,
        modifier = modifier.size(96.dp),
        shape = CircleShape,
    ) {
        Text("🎙", style = MaterialTheme.typography.headlineLarge)
    }
}

/** M2 요소 3 — 오늘의 회고 질문 카드. 탭하면 M3(자서전 작가 모드)로 진입해야 하지만
 * 진입 경로는 [MicButton]과 같은 사유로 아직 고정 라우팅. */
@Composable
private fun QuestionCard(question: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("오늘의 회고 질문", style = MaterialTheme.typography.labelLarge)
            Spacer(Modifier.height(8.dp))
            Text(question, style = MaterialTheme.typography.bodyLarge)
        }
    }
}

/** M2 요소 4 — 자서전 진행률·연속 대화일수·미회고 사진 수. `stats`가 아직 로딩 전이면
 * 빈 값(0/―) 대신 아무것도 그리지 않는다(깜빡임 방지). */
@Composable
private fun StatRow(stats: HomeStats?) {
    if (stats == null) return
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceEvenly,
    ) {
        StatItem(stats.completedChapters.toString(), "완성 챕터")
        StatItem("${stats.conversationStreakDays}일", "연속 대화")
        StatItem(stats.unrecalledPhotoCount.toString(), "미회고 사진")
    }
}

@Composable
private fun StatItem(
    value: String,
    label: String,
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.titleLarge)
        Text(label, style = MaterialTheme.typography.labelMedium)
    }
}

@Preview(showBackground = true)
@Composable
private fun HomeScreenPreview() {
    HomeScreen()
}
