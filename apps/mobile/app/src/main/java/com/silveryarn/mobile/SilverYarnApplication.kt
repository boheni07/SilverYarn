package com.silveryarn.mobile

import android.app.Application

/**
 * 앱 진입점 — 지금은 Room DB lazy 초기화 정도만 책임진다.
 *
 * TODO(Do 단계): 앱 시작 시 [com.silveryarn.mobile.installmode.InstallModeResolver]로
 * 설치모드를 재확인해 device_state 테이블과 동기화하는 로직 추가.
 */
class SilverYarnApplication : Application() {
    override fun onCreate() {
        super.onCreate()
    }
}
