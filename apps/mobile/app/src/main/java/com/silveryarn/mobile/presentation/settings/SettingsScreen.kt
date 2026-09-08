package com.silveryarn.mobile.presentation.settings

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 설정 화면 — 일반 모드에서만 노출(키오스크는 COSU lockTask로 설정 접근 자체를
 * 제한하는 게 정책 의도, decisions.md #6). Wi-Fi 등록은 여기서 이뤄지고
 * SSID는 device_state에만 로컬 저장한다(#22, 서버 미전송).
 */
@Composable
fun SettingsScreen(modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        Text("설정 — 준비 중")
    }
}
