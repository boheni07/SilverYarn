package com.silveryarn.mobile.local.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/** mobile-schema.md §2.6 `device_state` — 단일 행 테이블. 문서에는 PK가 명시돼
 * 있지 않지만 Room 엔티티는 PK가 필수라 고정값 [id]=0을 이 스캐폴딩에서 추가했다
 * (싱글턴 설정 테이블에 흔한 패턴 — INSERT OR REPLACE로 항상 그 한 행만 갱신). */
@Entity(tableName = "device_state")
data class DeviceStateEntity(
    @PrimaryKey val id: Int = 0,
    // POST /devices 등록 응답의 서버 devices.id — mobile-schema.md v0.4 신규(sync/SyncWorker
    // 참조: 이 값 없이는 어떤 동기화 호출도 자기 device_id를 못 보냄).
    @ColumnInfo(name = "device_id") val deviceId: String?,
    // "kiosk" | "normal"
    @ColumnInfo(name = "install_mode") val installMode: String,
    // 로컬 전용, 서버 미전송(decisions.md #22)
    @ColumnInfo(name = "registered_wifi_ssid") val registeredWifiSsid: String?,
    @ColumnInfo(name = "slm_model_version") val slmModelVersion: String?,
    @ColumnInfo(name = "prompt_pack_version") val promptPackVersion: String?,
    @ColumnInfo(name = "last_sync_at") val lastSyncAt: Long?,
    // GET /sync/download 응답의 sync_version을 그대로 저장해 다음 since로 되돌려
    // 보내는 불투명 커서(mobile-schema.md v0.5, sync-contract.md §5) — last_sync_at
    // (epoch ms)만으로는 서버 발급 형식을 재구성할 수 없어 별도로 둔다.
    @ColumnInfo(name = "last_sync_version") val lastSyncVersion: String?,
    // 온보딩 POST /users 요청에 쓴 이름 그대로 로컬 보관(mobile-schema.md v0.10, 신규) —
    // 서버는 이 값을 되돌려주지 않고(POST /devices 응답엔 없음), 홈 화면(M2) 인사말
    // "안녕하세요, OOO님"에 필요해 온보딩 시점에 같이 저장한다.
    @ColumnInfo(name = "user_name") val userName: String?,
)
