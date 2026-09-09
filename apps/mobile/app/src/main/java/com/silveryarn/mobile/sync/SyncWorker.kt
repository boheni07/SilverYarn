package com.silveryarn.mobile.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

/**
 * Wi-Fi 배치 동기화 워커 — decisions.md 확정 항목("등록 Wi-Fi 한정, 접속 즉시 자동
 * 트리거, 데이터 제한 없음"). 실제 트리거 등록(ConnectivityManager.NetworkCallback +
 * 등록 SSID 비교, decisions.md #22)은 아직 없다 — 이 워커는 WorkManager가 실제로
 * 실행할 작업 단위만 정의한다.
 *
 * 동기화 절차 본체는 [SyncRunner]에 있다(최초 동기화 화면과 공유). 이 클래스는
 * [SyncOutcome]을 WorkManager의 [Result]로 옮기는 얇은 어댑터다.
 * - [SyncOutcome.NotRegistered] → `Result.failure()` (온보딩 전, 재시도 무의미)
 * - [SyncOutcome.Completed] → `Result.success()` (download 실패는 다음 주기 재시도)
 *
 * TODO(Do 단계): Wi-Fi 등록 SSID 매칭 후 enqueue하는 트리거 로직(별도 net/ 패키지),
 * raw_audio_ref 업로드 계약 확정 시 [SyncRunner] 교체.
 */
class SyncWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result =
        when (SyncRunner(applicationContext).runOnce()) {
            is SyncOutcome.Completed -> Result.success()
            SyncOutcome.NotRegistered -> Result.failure()
        }
}
