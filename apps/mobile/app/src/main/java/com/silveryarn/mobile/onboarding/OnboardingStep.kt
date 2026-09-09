package com.silveryarn.mobile.onboarding

/**
 * 온보딩 선형 흐름의 단계. 상태 호이스팅(sealed + `when`)으로 전환하며, Navigation
 * 프레임워크는 화면이 늘면 재검토한다(nav 아키텍처 미도입, 결정 2026-09-09).
 *
 * design.md §2.9: 설치모드 자동분기 → 이름 입력 → 개인정보 수집 동의 → (createUser →
 * POST /devices → recordConsent) → 가족 초대 → 최초 동기화. 여기서는 이름·동의·서버
 * 3연쇄까지 다룬다(가족 초대·동기화는 이후 화면).
 */
sealed interface OnboardingStep {
    /** 어르신 이름(필수)·생년월일(선택, ISO yyyy-MM-dd) 입력. */
    object EnterName : OnboardingStep

    /** 개인정보 수집 동의. 동의해야 다음으로 진행한다. */
    object Consent : OnboardingStep

    /** createUser → POST /devices(토큰·install_mode 발급) → recordConsent 순차 실행 중. */
    object Submitting : OnboardingStep

    /** 완료 — install_mode에 따른 진입 분기는 MainActivity 책임. */
    data class Done(val installMode: String) : OnboardingStep

    /** 실패 — 동의 단계로 돌아가 재시도할 수 있다. */
    data class Failed(val message: String) : OnboardingStep
}
