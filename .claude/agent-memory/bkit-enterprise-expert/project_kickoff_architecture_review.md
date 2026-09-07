---
name: project-kickoff-architecture-review
description: 2026-09-05 CTO 리뷰보드에서 나온 SilverYarn Design v0.2 아키텍처 착수 판정(Go with conditions)과 6개 Blocker 요약
metadata:
  type: project
---

2026-09-05 개발 킥오프 전 아키텍처 심사 결과: **Go with conditions**. Design v0.2는 "무엇을 만들지"는 충분하나 "어떻게 분산·동기화·보호할지"가 비어 있다는 판정. 리포트는 파일로 남기지 않았으므로 아래가 유일한 기록이다.

착수 전 해소 필요 Blocker 6건:
- B1 동기화 계약 부재 — "최근 5일" 로컬 보존창(기획서 3.5)과 미동기화분 보존 규칙이 충돌해 장기 오프라인 시 구술 영구 소실. Server-Wins(design §6.1)가 엔티티 무차별 적용이라 device-origin 데이터(schedule_items 등) 유실.
- B2 온디바이스 SLM 모델 미선정 — 모바일 Phase 1 크리티컬 패스 전체가 대기.
- B3 6개 마이크로서비스 분해가 실 바운디드 컨텍스트 근거 없음 + 단일 PG/단일 Alembic 체인 + 작업 큐/Redis가 스택에 아예 없음. 권고: Phase 1은 api/worker 2 프로세스 모듈러 모놀리스.
- B4 이중 두뇌 — 흐름도 2.3(서버 CareAgent가 TTS 응답 생성)과 offline-first 원칙이 모순, 서버 실시간 대화 경로 존재 여부 자체가 미정. 프롬프트/페르소나 배포 채널도 없어 APK 재배포 없이는 페르소나 변경 불가.
- B5 PII 암호화 방식(서버 pgcrypto vs 앱레벨, 온디바이스 SQLCipher) 미정 — 전 리포지토리 소급 비용.
- B6 온프레미스 단일 사이트 DR — 백업 대상이 동일 MinIO(동일 실패 도메인)인데 단말은 5일 후 원본 삭제 → 복구 불가.

**Why:** design-validator의 문서 정합성 패스(33건)는 이 6건을 잡지 못했다. 문서 간 모순이 아니라 "어느 문서에도 없는 결정"이기 때문.
**How to apply:** Do 단계 코드 작성 요청이 오면 해당 영역의 Blocker가 닫혔는지 먼저 확인할 것. 특히 services/ 스캐폴딩 요청은 B3 결론(모놀리스 vs 6서비스)이 확정되기 전에는 진행하지 말 것. 관련: [[silveryarn-zero-egress-constraint]]
