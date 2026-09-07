"""schedule 모듈 — 비서 모드(일정/복약).

schedule_items: 4계층 구현 완료 — 다른 모듈과 동일한 참조 패턴이나, chapters/
conversation_chunks와 달리 POST 생성을 공개로 노출한다. AI 파이프라인 산출물이
아니라 가족·당사자가 직접 입력하는 리소스이기 때문이다.

`respond()`는 Chapter.ensure_reviewable()과 같은 재응답 방지 원칙(pending만
응답 가능)을 적용한다. sync-contract.md §3의 필드 단위 충돌정책(콘텐츠는
Server-Wins, 완료 표시는 Device-Wins)은 sync 모듈이 아직 골격 단계라 실제
동기화 병합 로직에는 반영되지 않았다 — TODO(다음 스프린트: sync 모듈 구현 시).
"""
