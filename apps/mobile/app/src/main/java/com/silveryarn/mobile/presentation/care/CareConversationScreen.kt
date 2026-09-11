package com.silveryarn.mobile.presentation.care

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 말벗돌봄 모드 — 정서 모니터링 파이프라인은 Phase 1 피처플래그 OFF
 * (decisions.md #25) — 이 화면은 대화 UI만 다루고 emotion_scores 관련 UI는
 * 피처플래그가 켜진 뒤 별도 구현.
 *
 * @param onEndSession [com.silveryarn.mobile.presentation.AppShell]이 "대화" 탭의
 *   마이크 세션을 끝내고 홈(M2)으로 되돌아갈 때 부르는 콜백 — 실제 발화 종료 감지
 *   ([com.silveryarn.mobile.ondevice.stt.SttEngine] VAD)가 붙기 전까지의 임시 UI.
 */
@Composable
fun CareConversationScreen(
    modifier: Modifier = Modifier,
    onEndSession: () -> Unit = {},
) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        Text("말벗돌봄 모드 — 준비 중")
        TextButton(onClick = onEndSession) {
            Text("대화 마치기")
        }
    }
}
