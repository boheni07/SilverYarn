package com.silveryarn.mobile.ondevice.stt

/**
 * 온디바이스 STT 엔진 계약 — CONVENTIONS.md §2.2.1: 구체 엔진(Sherpa-ONNX 등)은
 * 아직 "후보"이고 최종 선정은 실기기 벤치마크 대기 상태라 인터페이스만 둔다.
 * VAD가 800ms 묵음(decisions.md #31)을 판정해 발화 종료로 넘긴 오디오 버퍼를 받아
 * 텍스트로 변환하는 것이 책임의 전부 — 의도분류·SLM 라우팅은 여기서 하지 않는다.
 */
interface SttEngine {
    /** @param pcmAudio 16kHz mono PCM 버퍼(원본 저장 포맷인 Opus와는 별개 — 인코딩 전 원시 프레임) */
    suspend fun transcribe(pcmAudio: ByteArray): String
}
