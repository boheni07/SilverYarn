package com.silveryarn.mobile.installmode

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * decisions.md #5 임계값 — services/backend의 test_install_mode.py와 동일한
 * 경계값 세트를 검증한다(서버·기기 판정이 어긋나지 않아야 함, InstallModeResolver.kt
 * 클래스 docstring 참조).
 *
 * ⚠️ 이 테스트는 이 스캐폴딩 시점에 JDK/Gradle이 없어 실행하지 못했다
 * (apps/mobile/README.md "환경 제약" 참조) — services/backend의 순수 로직
 * 테스트와 동일한 케이스 구성이라 로직 정확성은 그쪽에서 대신 검증된 상태.
 */
class InstallModeResolverTest {
    @Test
    fun `RAM 미달만이면 키오스크`() {
        assertEquals(InstallMode.KIOSK, InstallModeResolver.resolve(ramGb = 4.0, androidSdkInt = 33)) // Android 13
    }

    @Test
    fun `Android 버전 미달만이면 키오스크`() {
        assertEquals(InstallMode.KIOSK, InstallModeResolver.resolve(ramGb = 8.0, androidSdkInt = 29)) // Android 10
    }

    @Test
    fun `둘_다_미달이면_키오스크`() {
        assertEquals(InstallMode.KIOSK, InstallModeResolver.resolve(ramGb = 3.0, androidSdkInt = 28)) // Android 9
    }

    @Test
    fun `둘_다_충족하면_일반`() {
        assertEquals(InstallMode.NORMAL, InstallModeResolver.resolve(ramGb = 8.0, androidSdkInt = 33))
    }

    @Test
    fun `경계값 — 6GB는 미달 아님, API 30은 초과 아님`() {
        assertEquals(InstallMode.NORMAL, InstallModeResolver.resolve(ramGb = 6.0, androidSdkInt = 31)) // Android 12
    }

    @Test
    fun `경계값 — API 30 정확히는 키오스크(11 이하)`() {
        assertEquals(InstallMode.KIOSK, InstallModeResolver.resolve(ramGb = 8.0, androidSdkInt = 30)) // Android 11
    }
}
