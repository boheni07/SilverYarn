package com.silveryarn.mobile.presentation.author

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 자서전 작가 모드 — 구술 인터뷰 화면 placeholder. 실제 대화 UI는
 * [com.silveryarn.mobile.ondevice] VAD/STT/SLM 파이프라인이 붙은 뒤 구현.
 */
@Composable
fun AuthorInterviewScreen(modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        Text("자서전 작가 모드 — 준비 중")
    }
}
