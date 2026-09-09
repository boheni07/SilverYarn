package com.silveryarn.mobile.presentation.sync

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.silveryarn.mobile.sync.SyncOutcome
import com.silveryarn.mobile.sync.SyncRunner

private sealed interface FirstSyncUi {
    object Running : FirstSyncUi

    object Done : FirstSyncUi

    data class Problem(val message: String) : FirstSyncUi
}

/**
 * 온보딩 직후 최초 Wi-Fi 동기화 화면 — design.md §2.9의 마지막 단계("최초 Wi-Fi
 * 동기화 → 첫 구술 인터뷰 시작"). [SyncRunner]를 1회 돌려 서버의 자서전 스냅샷·
 * 질문 큐·일정을 로컬 캐시에 채운 뒤 홈으로 넘긴다.
 *
 * 실패해도 앱은 오프라인으로 쓸 수 있으므로 "건너뛰기"로 홈에 진입할 수 있다 —
 * 다음 Wi-Fi 접속 시 [com.silveryarn.mobile.sync.SyncWorker]가 다시 시도한다.
 *
 * @param onDone 동기화 성공 또는 사용자가 건너뛰기를 눌렀을 때.
 */
@Composable
fun FirstSyncScreen(
    modifier: Modifier = Modifier,
    onDone: () -> Unit = {},
) {
    val context = LocalContext.current
    var ui by remember { mutableStateOf<FirstSyncUi>(FirstSyncUi.Running) }

    LaunchedEffect(ui) {
        when (ui) {
            FirstSyncUi.Running ->
                ui =
                    when (SyncRunner(context).runOnce()) {
                        is SyncOutcome.Completed -> FirstSyncUi.Done
                        SyncOutcome.NotRegistered ->
                            FirstSyncUi.Problem("기기 등록이 끝나지 않았습니다. 잠시 후 다시 시도해 주세요.")
                    }

            FirstSyncUi.Done -> onDone()
            is FirstSyncUi.Problem -> Unit
        }
    }

    Column(
        modifier =
            modifier
                .fillMaxSize()
                .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("은빛실타래", style = MaterialTheme.typography.headlineMedium)

        when (val current = ui) {
            FirstSyncUi.Running -> {
                CircularProgressIndicator()
                Text("어르신의 자서전과 오늘의 질문을 불러오는 중입니다…")
            }

            FirstSyncUi.Done ->
                Text("준비가 끝났습니다.")

            is FirstSyncUi.Problem -> {
                Text("동기화에 실패했습니다.")
                Text(current.message)
                Spacer(Modifier.height(8.dp))
                Button(onClick = { ui = FirstSyncUi.Running }, modifier = Modifier.fillMaxWidth()) {
                    Text("다시 시도")
                }
                TextButton(onClick = onDone, modifier = Modifier.fillMaxWidth()) {
                    Text("건너뛰기")
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun FirstSyncScreenPreview() {
    FirstSyncScreen()
}
