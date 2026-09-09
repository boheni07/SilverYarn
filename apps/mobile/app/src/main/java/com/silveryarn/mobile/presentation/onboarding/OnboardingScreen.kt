package com.silveryarn.mobile.presentation.onboarding

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.silveryarn.mobile.onboarding.OnboardingCoordinator
import com.silveryarn.mobile.onboarding.OnboardingStep

/**
 * 온보딩 흐름 — 상태 호이스팅(sealed [OnboardingStep] + `when`)으로 단계 전환.
 * Navigation 프레임워크·ViewModel은 미도입(결정 2026-09-09) — 화면이 늘면 재검토.
 *
 * ⚠️ 단계 상태는 `remember`라 프로세스 사망/구성 변경 시 처음으로 돌아간다 —
 * 스캐폴딩 수준에서 감수. rememberSaveable + Saver는 흐름이 확정되면 추가.
 *
 * @param onComplete 성공 시 서버가 판정한 install_mode("kiosk"|"normal")를 넘긴다.
 */
@Composable
fun OnboardingScreen(
    modifier: Modifier = Modifier,
    onComplete: (installMode: String) -> Unit = {},
) {
    val context = LocalContext.current
    val coordinator = remember { OnboardingCoordinator(context) }

    var step by remember { mutableStateOf<OnboardingStep>(OnboardingStep.EnterName) }
    var name by remember { mutableStateOf("") }
    var birthDate by remember { mutableStateOf("") }

    LaunchedEffect(step) {
        if (step is OnboardingStep.Submitting) {
            coordinator
                .run(name, birthDate.ifBlank { null })
                .onSuccess { step = OnboardingStep.Done(it) }
                .onFailure { step = OnboardingStep.Failed(it.message ?: "알 수 없는 오류") }
        }
    }

    Column(
        modifier =
            modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("은빛실타래", style = MaterialTheme.typography.headlineMedium)

        when (val current = step) {
            OnboardingStep.EnterName ->
                EnterNameStep(
                    name = name,
                    birthDate = birthDate,
                    onNameChange = { name = it },
                    onBirthDateChange = { birthDate = it },
                    onNext = { step = OnboardingStep.Consent },
                )

            OnboardingStep.Consent ->
                ConsentStep(
                    onAgree = { step = OnboardingStep.Submitting },
                    onBack = { step = OnboardingStep.EnterName },
                )

            OnboardingStep.Submitting -> SubmittingStep()

            is OnboardingStep.Done -> {
                LaunchedEffect(Unit) { onComplete(current.installMode) }
                Text("설정이 완료되었습니다. (${current.installMode})")
            }

            is OnboardingStep.Failed ->
                FailedStep(message = current.message, onRetry = { step = OnboardingStep.Consent })
        }
    }
}

@Composable
private fun EnterNameStep(
    name: String,
    birthDate: String,
    onNameChange: (String) -> Unit,
    onBirthDateChange: (String) -> Unit,
    onNext: () -> Unit,
) {
    Text("어르신 정보를 입력해 주세요.")
    OutlinedTextField(
        value = name,
        onValueChange = onNameChange,
        label = { Text("이름") },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    OutlinedTextField(
        value = birthDate,
        onValueChange = onBirthDateChange,
        label = { Text("생년월일 (선택, 예: 1945-03-12)") },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(8.dp))
    Button(onClick = onNext, enabled = name.isNotBlank(), modifier = Modifier.fillMaxWidth()) {
        Text("다음")
    }
}

@Composable
private fun ConsentStep(
    onAgree: () -> Unit,
    onBack: () -> Unit,
) {
    Text("개인정보 수집·이용 동의")
    Text(
        "구술 음성과 전사 텍스트, 사진, 일정 정보를 은빛실타래 서비스 제공 목적으로 수집·보관합니다. " +
            "이 정보는 온프레미스 서버에만 저장되며 동의를 철회하실 수 있습니다.",
    )
    Spacer(Modifier.height(8.dp))
    Button(onClick = onAgree, modifier = Modifier.fillMaxWidth()) { Text("동의하고 시작하기") }
    TextButton(onClick = onBack, modifier = Modifier.fillMaxWidth()) { Text("이전") }
}

@Composable
private fun SubmittingStep() {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        CircularProgressIndicator()
        Spacer(Modifier.height(12.dp))
        Text("계정을 만들고 기기를 등록하는 중입니다…")
    }
}

@Composable
private fun FailedStep(
    message: String,
    onRetry: () -> Unit,
) {
    Text("설정 중 문제가 발생했습니다.")
    Text(message)
    Spacer(Modifier.height(8.dp))
    Button(onClick = onRetry, modifier = Modifier.fillMaxWidth()) { Text("다시 시도") }
}

@Preview(showBackground = true)
@Composable
private fun OnboardingScreenPreview() {
    OnboardingScreen()
}
