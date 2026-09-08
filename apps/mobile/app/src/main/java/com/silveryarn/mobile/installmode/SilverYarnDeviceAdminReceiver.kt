package com.silveryarn.mobile.installmode

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent

/**
 * decisions.md #6 Device Owner Mode(COSU)의 진입점 — 이 리시버가 활성화돼야
 * [android.app.admin.DevicePolicyManager.isDeviceOwnerApp]이 true가 되고
 * lockTask(키오스크 잠금) API를 쓸 수 있다.
 *
 * ⚠️ 실기기 zero-touch/QR 프로비저닝(재활용 단말 공장초기화 후 최초 계정 설정
 * 시점 자동 등록)은 실제 기기·MDM 인프라가 있어야 검증 가능해 스캐폴딩 범위 밖이다
 * — 여기서는 콜백 진입점만 둔다. TODO(Do 단계): onEnabled에서 InstallModeResolver
 * 판정 결과가 KIOSK일 때만 lockTask 화이트리스트를 실제로 설정.
 */
class SilverYarnDeviceAdminReceiver : DeviceAdminReceiver() {
    override fun onEnabled(context: Context, intent: Intent) {
        super.onEnabled(context, intent)
    }
}
