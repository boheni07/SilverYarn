package com.silveryarn.mobile.presentation.photos

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.silveryarn.mobile.photos.PhotoUploadService
import kotlinx.coroutines.launch
import java.io.File

private sealed interface UploadState {
    data object Idle : UploadState

    data object Uploading : UploadState

    data object Success : UploadState

    data class Failed(
        val message: String,
    ) : UploadState
}

/**
 * M-05 "사진 추가하기"(신규, design.md §5.1 화면 인벤토리에 이름만 있고 실제 화면이
 * 없던 유일한 항목 — report.md §7 다음 사이클 권고 1순위). decisions.md #10 — 카메라
 * 즉시촬영 + 갤러리 선택 모두 지원, 업로드 전 리사이즈·압축은 [PhotoUploadService]가
 * 담당한다.
 *
 * 카메라·갤러리 둘 다 시스템 앱에 위임한다(`ActivityResultContracts.TakePicture`/
 * `PickVisualMedia`) — 콜백이 돌아온 시점엔 이미 사용자가 시스템 UI에서 사진을
 * 확정(또는 재촬영)한 뒤이므로, 이 화면에서 별도 "미리보기 확인" 단계를 두지 않고
 * 곧장 업로드한다(어르신 UX 원칙: 단계 최소화 — CompanionScreen이 발화를 즉시
 * 처리하는 것과 같은 방향).
 *
 * @param onBack [com.silveryarn.mobile.presentation.companion.CompanionScreen]으로 복귀.
 */
@Composable
fun PhotoUploadScreen(
    modifier: Modifier = Modifier,
    onBack: () -> Unit = {},
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val service = remember { PhotoUploadService(context) }

    var state by remember { mutableStateOf<UploadState>(UploadState.Idle) }
    var pendingCameraUri by remember { mutableStateOf<Uri?>(null) }

    fun startUpload(uri: Uri) {
        state = UploadState.Uploading
        scope.launch {
            val result = service.upload(uri)
            state =
                result.fold(
                    onSuccess = { UploadState.Success },
                    onFailure = { UploadState.Failed(it.message ?: "업로드 중 문제가 발생했습니다.") },
                )
        }
    }

    val galleryLauncher =
        rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
            if (uri != null) startUpload(uri)
        }
    val cameraLauncher =
        rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { captured ->
            val uri = pendingCameraUri
            if (captured && uri != null) startUpload(uri)
        }

    Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
        TextButton(onClick = onBack) { Text("← 대화로 돌아가기") }
        Spacer(Modifier.height(8.dp))
        Text("사진 추가하기", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(24.dp))

        when (val current = state) {
            UploadState.Idle -> {
                Button(
                    onClick = {
                        val uri = createCameraOutputUri(context)
                        pendingCameraUri = uri
                        cameraLauncher.launch(uri)
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("📷 사진 찍기") }
                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = {
                        galleryLauncher.launch(
                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly),
                        )
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("🖼 갤러리에서 선택") }
            }
            UploadState.Uploading -> {
                CircularProgressIndicator()
                Spacer(Modifier.height(12.dp))
                Text("업로드 중이에요…")
            }
            UploadState.Success -> {
                Text("사진을 잘 받았어요! 다음에 은실이가 이 사진 이야기를 물어볼 거예요.")
                Spacer(Modifier.height(16.dp))
                Button(onClick = onBack) { Text("대화로 돌아가기") }
            }
            is UploadState.Failed -> {
                Text(current.message)
                Spacer(Modifier.height(16.dp))
                Button(onClick = { state = UploadState.Idle }) { Text("다시 시도") }
            }
        }
    }
}

/** [FileProvider]로 카메라 결과물을 받을 임시 파일 Uri 생성 — 앱 캐시 디렉터리 아래
 * (`res/xml/file_paths.xml`의 `cache-path` 선언과 대응). 매 호출 새 파일명이라 이전
 * 촬영 결과와 섞이지 않는다. 이 앱은 `ActivityResultContracts.TakePicture()`로 시스템
 * 카메라 앱에 위임하는 방식이라 별도 `CAMERA` 런타임 권한은 필요 없다. */
private fun createCameraOutputUri(context: Context): Uri {
    val dir = File(context.cacheDir, "photos").apply { mkdirs() }
    val file = File(dir, "capture_${System.currentTimeMillis()}.jpg")
    return FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
}
