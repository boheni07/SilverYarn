package com.silveryarn.mobile.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.silveryarn.mobile.presentation.companion.CompanionScreen
import com.silveryarn.mobile.presentation.settings.SettingsScreen

/**
 * 온보딩·최초 동기화가 끝난 뒤([AppEntry]의 `AppState.Home`) 보여주는 홈 셸.
 *
 * **2026-09-13 개편(사용자 요청)**: 하단 4탭(대화/자서전/일정/설정, PR #23)을 걷어내고
 * [CompanionScreen] 하나로 통합했다 — "어르신의 모든 조작이 대화로 가능해야 한다"는
 * 요구에 따라, 자서전 작가모드·비서모드가 하던 일도 이제 은실이가 대화 중에 스스로
 * 꺼낸다(design.md §2.10 페르소나 통일). 설정만은 대화로 표현하기 애매한 기기 설정
 * (Wi-Fi 등록 등)이라 예외적으로 남겨두되, 상시 노출 탭이 아니라 [installMode]가
 * "normal"일 때만 보이는 아주 작은 텍스트 진입점으로 축소했다 — 키오스크 모드는
 * 원래도 Device Owner Mode(COSU) lockTask로 설정 접근 자체가 잠겨 있었다
 * (decisions.md #6). 일반 모드조차 어르신 본인이 아니라 기기를 설정해 준 가족이
 * 쓰는 경로라고 보고, 발견하기 쉬운 위치보다는 방해되지 않는 위치를 택했다.
 */
@Composable
fun AppShell(
    modifier: Modifier = Modifier,
    installMode: String = "kiosk",
) {
    var showSettings by remember { mutableStateOf(false) }

    if (showSettings) {
        SettingsScreen(modifier = modifier, onBack = { showSettings = false })
        return
    }

    Box(modifier = modifier.fillMaxSize()) {
        CompanionScreen(modifier = Modifier.fillMaxSize())

        if (installMode == "normal") {
            Text(
                "설정",
                style = MaterialTheme.typography.labelSmall,
                modifier =
                    Modifier
                        .align(Alignment.TopEnd)
                        .padding(12.dp)
                        .clickable { showSettings = true },
            )
        }
    }
}
