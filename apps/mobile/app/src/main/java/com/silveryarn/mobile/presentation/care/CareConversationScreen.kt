package com.silveryarn.mobile.presentation.care

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 말벗돌봄 모드 — 정서 모니터링 파이프라인은 Phase 1 피처플래그 OFF
 * (decisions.md #25) — 이 화면은 대화 UI만 다루고 emotion_scores 관련 UI는
 * 피처플래그가 켜진 뒤 별도 구현.
 */
@Composable
fun CareConversationScreen(modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        Text("말벗돌봄 모드 — 준비 중")
    }
}
