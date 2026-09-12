package com.silveryarn.mobile.benchmark

import com.silveryarn.mobile.ondevice.slm.SlmEngine
import com.silveryarn.mobile.ondevice.stt.SttEngine
import kotlinx.coroutines.flow.Flow

/**
 * decisions.md #27 — Kanana-2/Qwen2.5-0.5B 등 온디바이스 SLM 후보의 실제 추론 런타임
 * 연동(llama.cpp/MLC-LLM/ONNX Runtime Mobile 등 선정 자체도 미결)이 아직 없다는 걸
 * 코드 레벨에서 드러내기 위한 자리표시자 — [ConversationBenchmarkRunner]를 이 상태로
 * 돌리면 즉시 [NotImplementedError]로 실패해서, "벤치마크를 돌렸는데 숫자가 나왔다"는
 * 착각을 원천 차단한다. 실 벤치마크를 실행하려면 이 클래스가 아니라 실 구현체를
 * [RealDeviceBenchmarkTest](androidTest)에 연결해야 한다.
 */
class UnimplementedSttEngine : SttEngine {
    override suspend fun transcribe(pcmAudio: ByteArray): String {
        throw NotImplementedError(
            "SttEngine 실 구현체가 아직 없습니다 — 벤치마크 프로토콜 문서(ondevice-slm-benchmark-" +
                "protocol.md) §1 '준비물'을 먼저 완료하세요.",
        )
    }
}

/** [UnimplementedSttEngine] 참조. */
class UnimplementedSlmEngine : SlmEngine {
    override fun generateStreamed(
        userQuery: String,
        context: String,
    ): Flow<String> {
        throw NotImplementedError(
            "SlmEngine 실 구현체가 아직 없습니다 — 벤치마크 프로토콜 문서(ondevice-slm-benchmark-" +
                "protocol.md) §1 '준비물'을 먼저 완료하세요.",
        )
    }
}
