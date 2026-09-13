package com.silveryarn.mobile.ondevice.stt

import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MockSttEngineTest {
    @Test
    fun `호출마다 순환하며 다른 고정 문장을 반환`() =
        runBlocking {
            val engine = MockSttEngine()
            val first = engine.transcribe(ByteArray(0))
            val second = engine.transcribe(ByteArray(0))
            assertNotEquals(first, second)
        }

    @Test
    fun `pcmAudio 내용과 무관하게 항상 같은 순서로 순환`() =
        runBlocking {
            val withEmptyAudio = MockSttEngine()
            val withNonEmptyAudio = MockSttEngine()
            repeat(5) { index ->
                assertEquals(
                    withEmptyAudio.transcribe(ByteArray(0)),
                    withNonEmptyAudio.transcribe(ByteArray(16) { index.toByte() }),
                )
            }
        }

    @Test
    fun `목록 끝에 도달하면 처음으로 되돌아간다`() =
        runBlocking {
            val engine = MockSttEngine()
            val firstRound = List(SAMPLE_COUNT) { engine.transcribe(ByteArray(0)) }
            val secondRound = List(SAMPLE_COUNT) { engine.transcribe(ByteArray(0)) }
            assertEquals(firstRound, secondRound)
        }

    @Test
    fun `반환값은 항상 비어있지 않은 문자열`() =
        runBlocking {
            val engine = MockSttEngine()
            repeat(SAMPLE_COUNT) {
                assertTrue(engine.transcribe(ByteArray(0)).isNotBlank())
            }
        }

    companion object {
        // MockSttEngine.SAMPLE_TRANSCRIPTS는 private이라 값을 직접 참조할 수 없어
        // 순환 주기 검증용으로 그 크기(5개)를 여기 복제해 둔다.
        private const val SAMPLE_COUNT = 5
    }
}
