package com.silveryarn.mobile.presentation.assistant

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/** 비서 모드 — 일정/복약 리마인더. schedule_cache(local/db) 조회 UI는 아직 없음. */
@Composable
fun AssistantHomeScreen(modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        Text("비서 모드 — 준비 중")
    }
}
