import java.util.Properties

// ⚠️ 버전/설정 미검증 — apps/mobile/README.md "환경 제약" 참조. Android Studio에서
// 처음 열 때 AGP가 권장 버전으로 업그레이드를 제안하면 따르는 게 안전하다.

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.devtools.ksp") // Room 컴파일러
    id("org.jlleitschuh.gradle.ktlint")
}

// CONVENTIONS.md §4.1 — local.properties(Git 제외)에서 API_BASE_URL을 읽어
// BuildConfig 필드로 주입한다. 파일이 없으면(최초 clone 직후) 빈 문자열로 폴백—
// local.properties.example을 복사하라는 안내는 README.md 참조.
val localProperties = Properties().apply {
    val file = rootProject.file("local.properties")
    if (file.exists()) file.inputStream().use { load(it) }
}
val apiBaseUrl: String = localProperties.getProperty("API_BASE_URL", "")

android {
    namespace = "com.silveryarn.mobile"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.silveryarn.mobile"
        // decisions.md #5 키오스크 임계값(Android 11/API 30 이하 → 키오스크)이 지원
        // 대상의 하한을 사실상 규정한다 — minSdk는 그보다 더 낮은 API 26(Android 8.0)을
        // 잠정 하한으로 뒀다. 실기기 벤치마크(9장 잔여 항목) 전까지 미확정, TODO(Do 단계).
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        buildConfigField("String", "API_BASE_URL", "\"$apiBaseUrl\"")
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // --- Compose ---
    val composeBom = platform("androidx.compose:compose-bom:2024.09.03")
    implementation(composeBom)
    androidTestImplementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.9.2")
    debugImplementation("androidx.compose.ui:ui-tooling")

    // --- Room(SQLite, FTS5) — local/db, mobile-schema.md ---
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    // --- WorkManager — sync/SyncWorker ---
    implementation("androidx.work:work-runtime-ktx:2.9.1")

    // --- 서버 API 클라이언트 — sync/SyncApi (design.md §4.1 응답 포맷) ---
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.moshi:moshi:1.15.1")
    // @JsonClass(generateAdapter = true) 컴파일타임 codegen — 리플렉션 어댑터 불필요(RetrofitClient.kt 참조)
    ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.1")

    // --- 코루틴 ---
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")

    // --- 테스트 ---
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
}
