package com.silveryarn.mobile.presentation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.presentation.onboarding.OnboardingScreen
import com.silveryarn.mobile.presentation.sync.FirstSyncScreen

/** 앱 시작 시 목적지. */
private sealed interface AppState {
    /** `device_state` 조회 중. */
    object Loading : AppState

    /** 미등록 기기 — 온보딩부터. */
    object Onboarding : AppState

    /** 온보딩 직후 최초 Wi-Fi 동기화(design.md §2.9 마지막 단계). */
    data class FirstSync(val installMode: String) : AppState

    /** 등록 완료 — 홈. */
    data class Home(val installMode: String) : AppState
}

/**
 * 앱의 최상위 진입 지점 — [MainActivity]가 이것만 띄운다.
 *
 * 재시작 스킵: `device_state.device_id`가 있으면(= 이미 [OnboardingScreen] 3연쇄가
 * 끝났으면) 온보딩을 건너뛰고 바로 홈으로 간다. 없으면 온보딩 → 최초 동기화 → 홈.
 *
 * install_mode 분기: 확정된 모드("kiosk"|"normal")를 [onInstallModeResolved]로 올려
 * MainActivity가 [com.silveryarn.mobile.installmode.KioskController]로 lockTask를
 * 건다(decisions.md #6). 화면 자체는 두 모드가 동일(design.md §9.3) — 차이는 잠금뿐.
 *
 * ⚠️ 상태는 `remember`라 구성 변경 시 다시 로딩부터 — device_state 조회가 즉시라
 * 스캐폴딩 수준에서 감수. 등록 완료 후 홈은 [AppShell](M2 홈 + 하단 탭 4개)이 맡는다.
 */
@Composable
fun AppEntry(
    modifier: Modifier = Modifier,
    onInstallModeResolved: (String) -> Unit = {},
) {
    val context = LocalContext.current
    var state by remember { mutableStateOf<AppState>(AppState.Loading) }

    LaunchedEffect(Unit) {
        if (state != AppState.Loading) return@LaunchedEffect
        val deviceState = AppDatabase.getInstance(context).deviceStateDao().get()
        state =
            if (deviceState?.deviceId != null) {
                AppState.Home(deviceState.installMode)
            } else {
                AppState.Onboarding
            }
    }

    LaunchedEffect(state) {
        when (val current = state) {
            is AppState.FirstSync -> onInstallModeResolved(current.installMode)
            is AppState.Home -> onInstallModeResolved(current.installMode)
            else -> Unit
        }
    }

    when (val current = state) {
        AppState.Loading ->
            Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }

        AppState.Onboarding ->
            OnboardingScreen(
                modifier = modifier,
                onComplete = { installMode -> state = AppState.FirstSync(installMode) },
            )

        is AppState.FirstSync ->
            FirstSyncScreen(
                modifier = modifier,
                onDone = { state = AppState.Home(current.installMode) },
            )

        is AppState.Home -> AppShell(modifier = modifier)
    }
}
