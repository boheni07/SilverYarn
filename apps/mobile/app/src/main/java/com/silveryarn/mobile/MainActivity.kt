package com.silveryarn.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import com.silveryarn.mobile.installmode.KioskController
import com.silveryarn.mobile.presentation.AppEntry

/**
 * 앱 진입점. [AppEntry]가 시작 목적지를 정한다:
 * - `device_state.device_id` 있음 → 온보딩 스킵, 바로 홈
 * - 없음 → 온보딩 → 최초 Wi-Fi 동기화 → 홈
 *
 * install_mode 분기: [AppEntry]가 확정 모드를 올려주면 [KioskController]로 lockTask를
 * 건다(decisions.md #6, Device Owner가 아니면 조용히 무시). 화면 기능은 두 모드 동일.
 */
class MainActivity : ComponentActivity() {
    private val kioskController by lazy { KioskController(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface {
                    AppEntry(onInstallModeResolved = kioskController::apply)
                }
            }
        }
    }
}
