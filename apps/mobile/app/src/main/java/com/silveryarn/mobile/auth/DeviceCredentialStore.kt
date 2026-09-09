package com.silveryarn.mobile.auth

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Device Token(decisions.md #47) 보안 저장소.
 *
 * 서버는 `POST /devices` 응답으로 평문 토큰을 **1회만** 내려주고(이후 재조회 불가, 해시만
 * 보관) 클라이언트는 이후 모든 sync 요청의 `X-Device-Token` 헤더로 이 토큰을 쓴다.
 * 자격증명이므로 Room `device_state`가 아니라 Android Keystore로 마스터 키를 보호하는
 * [EncryptedSharedPreferences]에 저장한다(CONVENTIONS.md §4.1 — 기기별 민감 값은 보안 저장소).
 */
class DeviceCredentialStore private constructor(private val prefs: SharedPreferences) {
    fun saveToken(token: String) {
        prefs.edit().putString(KEY_TOKEN, token).apply()
    }

    fun token(): String? = prefs.getString(KEY_TOKEN, null)

    /** 분실·재프로비저닝 대비 — 서버 측 폐기(device_credentials.revoked_at)와 짝. */
    fun clear() {
        prefs.edit().remove(KEY_TOKEN).apply()
    }

    companion object {
        private const val PREFS_NAME = "silveryarn_device_credentials"
        private const val KEY_TOKEN = "device_token"

        @Volatile private var instance: DeviceCredentialStore? = null

        fun getInstance(context: Context): DeviceCredentialStore =
            instance ?: synchronized(this) {
                instance ?: build(context.applicationContext).also { instance = it }
            }

        private fun build(context: Context): DeviceCredentialStore {
            val masterKey =
                MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
            val prefs =
                EncryptedSharedPreferences.create(
                    context,
                    PREFS_NAME,
                    masterKey,
                    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
                )
            return DeviceCredentialStore(prefs)
        }
    }
}
