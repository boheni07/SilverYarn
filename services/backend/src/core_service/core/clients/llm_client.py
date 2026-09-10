"""온프레미스 vLLM 클라이언트 — design.md §2.11(지식추출·윤문), decisions.md #26.

vLLM의 OpenAI 호환 서버(`/v1/chat/completions`)를 그대로 쓴다고 가정한다 — 이
부분은 vLLM 공식 배포 형태라 다른 클라이언트(STT/Embedding)보다 신뢰도가 높다.

네 유스케이스만 지원한다:
- `extract_knowledge`: 청크 1건에서 인물·시기·장소·감정을 JSON으로 추출
  (workflow-diagrams.md §3 "지식 추출")
- `generate_chapter_draft`: 기존 챕터 본문 + 신규 구술을 문어체로 재구성
  (workflow-diagrams.md §3 "챕터 초안 윤문")
- `compact_chapter`: 확정 챕터 본문 → 온디바이스 FTS5용 요약·키워드 JSON
  (design.md §2.11 4단계 Compaction Engine)
- `critique_and_generate_questions`: 챕터 본문 + 최근 구술 → 서사 갭 분석 후
  심층 회고 질문 Top-3 JSON (design.md §2.11 3단계 Critic Agent,
  workflow-diagrams.md §4 "질문 이력 대조 → 신규/꼬리질문 생성")

⚠️ 전부 LLM에게 "JSON만 출력해라"/"문어체로 써라" 프롬프트로 요청하고 응답을
파싱한다 — vLLM 서버가 `response_format` 강제(structured output)를 지원하는지는
모델·버전에 따라 다르므로, 파싱 실패는 예외로 던지고 호출자가 best-effort로
처리하게 한다(예외를 여기서 삼키지 않음).
"""

import json
from typing import Any

import httpx

from core_service.core.config import get_settings

_EXTRACT_SYSTEM_PROMPT = (
    "다음 대화 구술 텍스트에서 인물·시기·장소·감정을 추출해 JSON으로만 답하라. "
    '형식: {"period": "childhood|youth|adulthood|present" 중 하나 또는 null, '
    '"people": ["이름", ...], "place": "장소 또는 null", "emotion": "감정 또는 null"}'
)

_CHAPTER_SYSTEM_PROMPT = (
    "너는 어르신의 구술을 자서전 문어체로 정리하는 작가다. 기존 챕터 본문에 "
    "새 구술 내용을 자연스럽게 이어붙여 하나의 문어체 문단으로 재구성하라. "
    "구술체 표현(음, 그, 저기 등)은 제거하고 존댓말 대신 서술체로 쓴다."
)

_COMPACT_SYSTEM_PROMPT = (
    "다음 자서전 챕터 본문을 온디바이스 검색용으로 압축해 JSON으로만 답하라. "
    '형식: {"summary": "2문장 이내 한국어 요약", '
    '"keywords": ["핵심어", ...]}. keywords는 5~10개, 인물·연도·장소·사건 위주로 '
    "본문에 실제로 나온 표현을 쓴다."
)

_CRITIC_SYSTEM_PROMPT = (
    "너는 어르신 자서전의 서사 완성도를 평가하는 에디터다. 주어진 챕터 본문과 최근 "
    "구술을 Fact(사실·연대)·Emotion(감정)·Relation(인물 관계)·Reflection(회고·의미) "
    "네 축으로 살펴, 가장 빈약한 축을 메울 심층 회고 질문을 최대 3개 만들어 JSON으로만 "
    "답하라. 이미 물어본 질문 목록이 주어지면 그와 겹치지 않게 한다. "
    '형식: {"questions": [{"text": "질문", "type": "new_topic 또는 follow_up"}, ...]}. '
    "type은 새 주제를 여는 질문이면 new_topic, 방금 구술을 더 파고드는 질문이면 follow_up. "
    "질문은 어르신께 드리는 존댓말 한 문장으로 쓴다."
)


class LLMClient:
    def __init__(self, endpoint: str | None = None, model: str | None = None, timeout: float = 60.0):
        settings = get_settings()
        self._endpoint = endpoint or settings.llm_endpoint
        self._model = model or settings.llm_model_name
        self._timeout = timeout

    async def _chat(self, system_prompt: str, user_content: str) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._endpoint}/chat/completions",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def extract_knowledge(self, transcript: str) -> dict[str, Any]:
        """실패(HTTP 오류·JSON 파싱 실패) 시 예외를 던진다 — 호출자가 처리."""
        raw = await self._chat(_EXTRACT_SYSTEM_PROMPT, transcript)
        return json.loads(raw)

    async def generate_chapter_draft(self, existing_body: str | None, new_transcript: str) -> str:
        user_content = (
            f"[기존 챕터 본문]\n{existing_body or '(신규 챕터, 기존 본문 없음)'}\n\n"
            f"[새 구술 내용]\n{new_transcript}"
        )
        return await self._chat(_CHAPTER_SYSTEM_PROMPT, user_content)

    async def compact_chapter(self, body_text: str) -> tuple[str, list[str]]:
        """확정 챕터 본문 → (요약, 키워드 목록). design.md §2.11 4단계.

        실패(HTTP 오류·JSON 파싱 실패·형식 불일치) 시 예외를 던진다 — 호출자가
        best-effort로 처리(파이프라인은 이전 요약 유지 또는 body_text 대체).
        """
        raw = await self._chat(_COMPACT_SYSTEM_PROMPT, body_text)
        parsed = json.loads(raw)
        summary = str(parsed["summary"]).strip()
        keywords = [str(k).strip() for k in parsed["keywords"] if str(k).strip()]
        if not summary:
            raise ValueError("compact_chapter: summary가 비어 있습니다.")
        return summary, keywords

    async def critique_and_generate_questions(
        self,
        chapter_body: str,
        latest_transcript: str,
        existing_question_texts: list[str],
    ) -> list[tuple[str, str]]:
        """서사 갭 분석 → 회고 질문 초안 목록 `[(text, type_str), ...]` (최대 3개).

        `type_str`은 "new_topic" 또는 "follow_up" — 검증은 호출자(QuestionService)가 한다.
        실패(HTTP 오류·JSON 파싱 실패·형식 불일치) 시 예외를 던진다.
        """
        already = "\n".join(f"- {t}" for t in existing_question_texts) or "(없음)"
        user_content = (
            f"[챕터 본문]\n{chapter_body}\n\n"
            f"[최근 구술]\n{latest_transcript}\n\n"
            f"[이미 물어본 질문]\n{already}"
        )
        raw = await self._chat(_CRITIC_SYSTEM_PROMPT, user_content)
        parsed = json.loads(raw)
        out: list[tuple[str, str]] = []
        for item in parsed["questions"][:3]:
            text = str(item["text"]).strip()
            qtype = str(item["type"]).strip()
            if text:
                out.append((text, qtype))
        return out
