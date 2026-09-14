package com.silveryarn.mobile.photos

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import com.silveryarn.mobile.auth.DeviceCredentialStore
import com.silveryarn.mobile.local.db.AppDatabase
import com.silveryarn.mobile.sync.RetrofitClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream

// decisions.md #10 — "업로드 전 클라이언트 측 리사이즈(장변 최대 1600px)·JPEG 80% 압축 적용".
// 재활용/저사양 단말의 저장용량·전송량 제약 때문에 온디바이스에만 적용한다 — apps/web의
// PhotoUploadForm은 가족이 스캔한 원본을 다루는 대상이라 이 정책 밖(그쪽 주석 참조).
private const val MAX_EDGE_PX = 1600
private const val JPEG_QUALITY = 80

/**
 * 모바일 "사진 추가하기" 화면(M-05, 신규)의 업로드 오케스트레이션 —
 * sync-contract.md §4 Presigned URL 3단계를 어르신 본인 기기(Device Token)로 수행한다.
 * `DeviceRegistrar`/`OnboardingCoordinator`와 동일하게 `Result<T>` + `runCatching`
 * 패턴을 쓴다(이 코드베이스에 아직 `ApiException`을 실제로 던지는 곳이 없어 그 관용을
 * 그대로 따름 — ApiEnvelope.error 필드는 검사하지 않고 `.data` null 여부만 본다).
 */
class PhotoUploadService(private val context: Context) {
    /** @param imageUri 카메라(TakePicture)로 찍었거나 갤러리(PickVisualMedia)에서 고른 원본 사진. */
    suspend fun upload(imageUri: Uri): Result<Unit> =
        withContext(Dispatchers.IO) {
            runCatching {
                val db = AppDatabase.getInstance(context)
                val deviceState = db.deviceStateDao().get() ?: error("기기 등록 정보가 없습니다.")
                val userId = deviceState.userId ?: error("어르신 계정 정보를 찾을 수 없습니다.")
                val deviceToken =
                    DeviceCredentialStore.getInstance(context).token() ?: error("Device Token이 저장되지 않았습니다.")

                val jpegBytes = compress(imageUri)

                val urlResult =
                    RetrofitClient.photosApi
                        .requestUploadUrl(
                            deviceToken = deviceToken,
                            body =
                                PhotoUploadUrlRequest(
                                    userId = userId,
                                    contentType = "image/jpeg",
                                    fileSize = jpegBytes.size,
                                ),
                        ).data ?: error("업로드 URL 발급에 실패했습니다.")

                val putResponse =
                    RetrofitClient.photosApi.putToPresignedUrl(
                        uploadUrl = urlResult.uploadUrl,
                        contentType = "image/jpeg",
                        body = jpegBytes.toRequestBody("image/jpeg".toMediaType()),
                    )
                if (!putResponse.isSuccessful) {
                    error("사진 업로드에 실패했습니다 (MinIO 응답 ${putResponse.code()}).")
                }

                RetrofitClient.photosApi.completeUpload(deviceToken = deviceToken, photoId = urlResult.photoId)
                Unit
            }
        }

    /** 장변 [MAX_EDGE_PX] 이하로 축소(원본이 더 작으면 확대하지 않음) + JPEG [JPEG_QUALITY]%
     * 압축 — decisions.md #10. 원본 포맷(JPEG/PNG/WEBP 어느 쪽이든)과 무관하게 항상
     * JPEG로 재인코딩해 내보낸다. */
    private fun compress(uri: Uri): ByteArray {
        val original =
            context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) }
                ?: error("이미지를 읽을 수 없습니다.")
        val longEdge = maxOf(original.width, original.height)
        val scale = MAX_EDGE_PX.toFloat() / longEdge
        val resized =
            if (scale < 1f) {
                Bitmap.createScaledBitmap(
                    original,
                    (original.width * scale).toInt().coerceAtLeast(1),
                    (original.height * scale).toInt().coerceAtLeast(1),
                    true,
                )
            } else {
                original
            }
        return ByteArrayOutputStream().use { stream ->
            resized.compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, stream)
            stream.toByteArray()
        }
    }
}
