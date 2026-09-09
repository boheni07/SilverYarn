package com.silveryarn.mobile.presentation.onboarding

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

/**
 * 스캐폴딩 단계 placeholder — 실제 온보딩 흐름(기기 등록 → 설치모드 자동분기 →
 * Wi-Fi 등록 → 어르신 계정 연결)은 UI/UX 화면설계서 기준으로 별도 구현 필요.
 * 지금은 모듈 구조(presentation/·installmode/·local/·ondevice/·sync/)가
 * 실제로 컴파일되는 것을 증명하는 최소 골격이다.
 *
 * 서버 계약은 [com.silveryarn.mobile.onboarding.OnboardingApi]에 고정돼 있다
 * (createUser → recordConsent, design.md §2.9). 화면 연결(네비게이션·상태 관리·
 * 동의 화면 UI)은 온보딩 네비게이션 아키텍처 확정 후 진행한다.
 */
@Composable
fun OnboardingScreen(modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        Text("은빛실타래")
        Text("스캐폴딩 단계 — 온보딩 화면 준비 중")
    }
}

@Preview(showBackground = true)
@Composable
private fun OnboardingScreenPreview() {
    OnboardingScreen()
}
