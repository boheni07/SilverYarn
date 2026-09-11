package com.silveryarn.mobile.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.silveryarn.mobile.presentation.assistant.AssistantHomeScreen
import com.silveryarn.mobile.presentation.author.AuthorInterviewScreen
import com.silveryarn.mobile.presentation.care.CareConversationScreen
import com.silveryarn.mobile.presentation.home.HomeScreen
import com.silveryarn.mobile.presentation.settings.SettingsScreen

/** M2/M5/M6 공통 하단 탭 4개(`wf-bottomnav`) — 자서전 작가모드(M3)는 "자서전" 탭으로,
 * 말벗돌봄 모드(M4)는 "대화" 탭의 마이크 세션으로 진입해 탭 목록에는 없다. */
private enum class BottomTab(val label: String) {
    CONVERSATION("대화"),
    AUTHOR("자서전"),
    SCHEDULE("일정"),
    SETTINGS("설정"),
}

/**
 * 온보딩·최초 동기화가 끝난 뒤([AppEntry]의 `AppState.Home`) 보여주는 홈 셸.
 *
 * "대화" 탭은 평소엔 [HomeScreen](마이크 대기)을 보여주다가 마이크를 탭하면 그
 * 탭 안에서 대화 세션(현재는 [CareConversationScreen] 고정)으로 전환된다 — 실제로는
 * 온디바이스 SLM 라우터가 자서전 작가 모드(M3)·말벗돌봄 모드(M4) 중 하나로 발화
 * 의도를 분류해야 하지만(workflow-diagrams.md §19 "에이전트 라우팅"), 그 라우터
 * ([com.silveryarn.mobile.ondevice.slm.SlmEngine])가 아직 스텁이라 지금은 고정
 * 목적지로 보낸다 — 라우터가 붙으면 이 분기만 교체하면 된다. 다른 탭 전환 시
 * 진행 중이던 세션은 끝난다(스캐폴딩 단계의 단순 규칙).
 */
@Composable
fun AppShell(modifier: Modifier = Modifier) {
    var tab by remember { mutableStateOf(BottomTab.CONVERSATION) }
    var conversationSessionActive by remember { mutableStateOf(false) }

    Column(modifier = modifier.fillMaxSize()) {
        Box(modifier = Modifier.weight(1f)) {
            when (tab) {
                BottomTab.CONVERSATION ->
                    if (conversationSessionActive) {
                        CareConversationScreen(onEndSession = { conversationSessionActive = false })
                    } else {
                        HomeScreen(onStartConversation = { conversationSessionActive = true })
                    }

                BottomTab.AUTHOR -> AuthorInterviewScreen()
                BottomTab.SCHEDULE -> AssistantHomeScreen()
                BottomTab.SETTINGS -> SettingsScreen()
            }
        }

        BottomNavBar(
            selected = tab,
            onSelect = { selected ->
                tab = selected
                conversationSessionActive = false
            },
        )
    }
}

@Composable
private fun BottomNavBar(
    selected: BottomTab,
    onSelect: (BottomTab) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceEvenly,
    ) {
        BottomTab.entries.forEach { entry ->
            TextButton(onClick = { onSelect(entry) }) {
                Text(
                    entry.label,
                    fontWeight = if (entry == selected) FontWeight.Bold else FontWeight.Normal,
                )
            }
        }
    }
}
