package com.silveryarn.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import com.silveryarn.mobile.presentation.onboarding.OnboardingScreen

/**
 * 스캐폴딩 단계 임시 진입점 — apps/web·apps/admin의 홈 화면과 같은 이유로,
 * 실제 온보딩/모드 분기 로직 전까지는 OnboardingScreen 하나만 띄운다.
 *
 * TODO(Do 단계): device_state.install_mode를 읽어 키오스크(COSU lockTask)면
 * 홈 화면으로 즉시 진입, 일반 모드면 실제 앱 목록에서 선택 가능하게 분기.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface {
                    OnboardingScreen()
                }
            }
        }
    }
}
