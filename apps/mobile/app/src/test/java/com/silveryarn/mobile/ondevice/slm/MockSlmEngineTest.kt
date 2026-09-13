package com.silveryarn.mobile.ondevice.slm

import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MockSlmEngineTest {
    @Test
    fun `여러 문장을 순서대로 스트리밍`() =
        runBlocking {
            val chunks = MockSlmEngine().generateStreamed(userQuery = "안녕하세요", context = "").toList()
            assertTrue(chunks.size >= 2)
        }

    @Test
    fun `날씨 언급 시 날씨 관련 응답`() =
        runBlocking {
            val chunks = MockSlmEngine().generateStreamed(userQuery = "오늘 날씨가 좋네요", context = "").toList()
            assertTrue(chunks.any { "산책" in it })
        }

    @Test
    fun `잠 언급 시 수면 관련 응답`() =
        runBlocking {
            val chunks = MockSlmEngine().generateStreamed(userQuery = "잠이 안 와요", context = "").toList()
            assertTrue(chunks.any { "햇볕" in it })
        }

    @Test
    fun `매칭되는 키워드가 없으면 기본 응답`() =
        runBlocking {
            val chunks = MockSlmEngine().generateStreamed(userQuery = "아무 말이나 해봤어요", context = "").toList()
            assertEquals(listOf("그러셨군요.", "오늘 하루는 어떠셨어요?"), chunks)
        }
}
