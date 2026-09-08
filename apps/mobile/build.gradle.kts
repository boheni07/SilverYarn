// 루트 빌드 스크립트 — 플러그인 버전만 선언(apply false), 실제 적용은 app/build.gradle.kts.
//
// ⚠️ 버전 확정 미검증: 이 저장소 환경에는 JDK/Android SDK/Gradle이 설치돼 있지 않아
// (스캐폴딩 시점 확인, apps/mobile/README.md 참조) 아래 버전 조합이 실제로 빌드되는지
// 확인하지 못했다. Kotlin 2.0/AGP 8.5는 2026년 시점 안정 버전대를 근거로 골랐지만,
// 실 Android Studio/Gradle 환경에서 첫 sync 시 재검증 필요.
plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "2.0.20" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.20" apply false
    id("com.google.devtools.ksp") version "2.0.20-1.0.25" apply false
    id("org.jlleitschuh.gradle.ktlint") version "12.1.1" apply false
}
