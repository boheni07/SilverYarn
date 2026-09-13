package com.silveryarn.mobile.presentation.settings

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 설정 화면 — [com.silveryarn.mobile.presentation.AppShell]의 아주 작은 텍스트
 * 진입점("normal" 설치모드에서만 노출)으로만 들어올 수 있다. 키오스크 모드는 원래도
 * COSU lockTask로 설정 접근 자체를 제한하는 게 정책 의도(decisions.md #6). Wi-Fi
 * 등록은 여기서 이뤄지고 SSID는 device_state에만 로컬 저장한다(#22, 서버 미전송).
 *
 * @param onBack 은실이와의 대화 화면([com.silveryarn.mobile.presentation.companion.CompanionScreen])으로
 * 돌아간다 — Navigation 프레임워크 미도입 방침(2026-09-09)에 따라 단순 콜백으로 처리.
 */
@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    onBack: () -> Unit = {},
) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        TextButton(onClick = onBack) { Text("← 대화로 돌아가기") }
        Text("설정 — 준비 중")
    }
}
