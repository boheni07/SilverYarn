package com.silveryarn.mobile.benchmark

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.silveryarn.mobile.ondevice.tts.AndroidNativeTtsEngine
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/**
 * decisions.md #27/#31 온디바이스 SLM 실기기 벤치마크의 실행 진입점 —
 * `docs/03-check/ondevice-slm-benchmark-protocol.md`가 SoR이다.
 *
 * ⚠️ **이 테스트는 CI에서 실행되지 않는다.** `ci.yml`의 apps/mobile job은
 * `assembleAndroidTest`(컴파일만)까지만 돌린다 — 실 기기의 발열·배터리·메모리
 * 압박을 흉내낼 방법이 없어 `connectedAndroidTest`(실행)는 물리 기기/에뮬레이터가
 * 붙어 있는 로컬 환경에서만 의미가 있다.
 *
 * **실행 전 준비 (프로토콜 문서 §1)**:
 * 1. [SlmEngine]/[SttEngine] 실 구현체를 만들어 아래 [UnimplementedSttEngine]/
 *    [UnimplementedSlmEngine] 자리를 교체한다.
 * 2. `app/src/androidTest/assets/benchmark_fixtures/`에 16kHz mono PCM 오디오
 *    샘플을 넣는다(파일명 무관, 확장자 `.pcm`). 없으면 이 테스트는 실패가 아니라
 *    **스킵**된다(아래 `assumeTrue` — "아직 준비 안 됨"과 "돌았는데 틀림"을 구분하기 위해).
 * 3. `./gradlew connectedAndroidTest --tests RealDeviceBenchmarkTest` 로 실행,
 *    결과는 기기의 `getExternalFilesDir(null)/benchmark/`에 CSV로 남는다 —
 *    `adb pull`로 꺼내 프로토콜 문서 §6 비교표에 붙여넣는다.
 */
@RunWith(AndroidJUnit4::class)
class RealDeviceBenchmarkTest {
    @Test
    fun runBenchmarkSession() =
        runBlocking {
            val instrumentation = InstrumentationRegistry.getInstrumentation()
            val appContext = instrumentation.targetContext

            // README.md는 안내 문서일 뿐 오디오가 아니므로 목록에서 제외한다.
            val fixtureNames =
                instrumentation.context.assets.list("benchmark_fixtures").orEmpty()
                    .filter { it.endsWith(".pcm") }
            assumeTrue(
                "benchmark_fixtures/*.pcm 샘플이 없습니다 — 프로토콜 문서 §1 준비물을 먼저 채우세요.",
                fixtureNames.isNotEmpty(),
            )

            val turns =
                fixtureNames.sorted().map { name ->
                    val pcm = instrumentation.context.assets.open("benchmark_fixtures/$name").use { it.readBytes() }
                    BenchmarkTurn(pcmAudio = pcm, slmContext = "")
                }

            // ⚠️ 준비 1번 항목 — 실 구현체가 생기면 이 두 줄만 교체.
            val stt = UnimplementedSttEngine()
            val slm = UnimplementedSlmEngine()
            val tts = AndroidNativeTtsEngine(appContext)

            val runner = ConversationBenchmarkRunner(stt, slm, tts, DeviceProfiler(appContext))
            // 실행할 후보 이름을 직접 채워 넣는다(예: "kanana-2-4bit").
            val slmCandidateName = "REPLACE_ME"
            val summary =
                runner.runSession(
                    deviceModel = android.os.Build.MODEL,
                    slmCandidate = slmCandidateName,
                    turns = turns,
                )

            val outDir = File(appContext.getExternalFilesDir(null), "benchmark").apply { mkdirs() }
            File(outDir, "${summary.deviceModel}_${summary.slmCandidate}_detail.csv")
                .writeText(CsvReportWriter.toDetailCsv(summary))
            File(outDir, "summary.csv").appendText(CsvReportWriter.toSummaryLine(summary) + "\n")
        }
}
