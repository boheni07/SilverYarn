package com.silveryarn.mobile.ondevice.slm

import kotlinx.coroutines.flow.Flow

/**
 * 온디바이스 SLM 엔진 계약 — decisions.md #27: Kanana-2/Qwen2.5-0.5B(4bit 양자화)
 * 벤치마크 후보 2종, 최종 선정은 실기기 벤치마크 대기. 응답을 [Flow]로 스트리밍
 * 반환하는 이유는 decisions.md #31 "문장 단위 SLM 스트리밍→TTS 파이프라이닝"
 * (전체 응답 완성을 기다리지 않고 첫 문장부터 즉시 합성) 때문이다.
 */
interface SlmEngine {
    /** @param context FTS5 검색(autobiography_fts) + 최근 대화 이력으로 구성한 프롬프트 컨텍스트 */
    fun generateStreamed(userQuery: String, context: String): Flow<String>
}
