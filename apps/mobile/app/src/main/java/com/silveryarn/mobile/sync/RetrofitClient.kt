package com.silveryarn.mobile.sync

import com.silveryarn.mobile.BuildConfig
import com.silveryarn.mobile.onboarding.OnboardingApi
import com.squareup.moshi.Moshi
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory

/** CONVENTIONS.md §4.1 — API_BASE_URL은 .env가 아니라 local.properties → BuildConfig로
 * 주입된다(app/build.gradle.kts 참조). apps/web·apps/admin의 NEXT_PUBLIC_API_URL과
 * 동일한 값을 가리키게 맞춘다(기본 http://127.0.0.1:8000, /api/v1는 여기서 붙인다).
 *
 * `@JsonClass(generateAdapter = true)`(ApiEnvelope.kt/SyncApi.kt)는 컴파일 타임
 * codegen이라(app/build.gradle.kts의 ksp("com.squareup.moshi:moshi-kotlin-codegen"))
 * 리플렉션 기반 KotlinJsonAdapterFactory를 따로 등록할 필요가 없다. */
object RetrofitClient {
    private val moshi = Moshi.Builder().build()

    private val retrofit: Retrofit by lazy {
        Retrofit
            .Builder()
            .baseUrl("${BuildConfig.API_BASE_URL}/api/v1/")
            .client(OkHttpClient.Builder().build())
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
    }

    val syncApi: SyncApi by lazy { retrofit.create(SyncApi::class.java) }

    val onboardingApi: OnboardingApi by lazy { retrofit.create(OnboardingApi::class.java) }
}
