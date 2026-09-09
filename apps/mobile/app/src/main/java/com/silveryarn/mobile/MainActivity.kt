package com.silveryarn.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.silveryarn.mobile.presentation.assistant.AssistantHomeScreen
import com.silveryarn.mobile.presentation.onboarding.OnboardingScreen

/**
 * 스캐폴딩 진입점. [OnboardingScreen]을 띄우고, 완료되면 홈으로 전환한다.
 *
 * TODO(Do 단계): ① 앱 재시작 시 `device_state.device_id` 유무로 온보딩 스킵 판정
 * (지금은 매번 온보딩). ② install_mode="kiosk"면 COSU lockTask 진입, "normal"이면
 * 3대 모드 선택 홈으로 분기(현재는 둘 다 AssistantHomeScreen 임시).
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface {
                    var onboarded by remember { mutableStateOf(false) }
                    if (onboarded) {
                        AssistantHomeScreen()
                    } else {
                        OnboardingScreen(onComplete = { onboarded = true })
                    }
                }
            }
        }
    }
}
