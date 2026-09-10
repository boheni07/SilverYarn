# PDCA Check #2 — 설계문서 ↔ 구현 갭 분석

> **Date**: 2026-09-11
> **범위**: 1차 Check(`gap-analysis-2026-09-10.md`, design v0.26/0.27) 이후 PR #10~19 반영. design v0.35 · schema.md v1.12 · 마이그레이션 0007 ↔ 실 구현·실 DB.
> **1차 이후 변경**: 모바일 앱 시작 게이트(#10), import-linter(#11), `core/auth.py` 순수화(#13), Compaction Engine(#15), Critic Agent(#16), apps/web 알림 설정 화면(#17), apps/web·apps/admin Keycloak 로그인(#18·#19), Do 사이클 보고서(#12)·법무 트래커(#14).

---

## 요약

| # | 구분 | 항목 | 조치 |
|---|---|---|---|
| G7 | 문서 드리프트 | design §11.2 Implementation Order 스테일 — item 1 "schema.md v1.11 / 마이그레이션 0001~0006", item 5 "Compaction Engine 미구현" | v0.36에서 v1.12/0007, Compaction·Critic Agent 구현 반영 ✅ |
| G8 | 문서 드리프트 | design §11.1 File Structure "Alembic 0001~0006" | v0.36에서 0001~0007 ✅ |
| G9 | 문서 드리프트 | structure.md 모듈 수 스테일 — 라인 30 "8개", §2 "10개 논리 모듈 전부" (`consent`·`notifications` 누락) | structure.md v1.35에서 "12개"로 정정 ✅ |
| G10 | 문서 드리프트 | structure.md §2 "`photos` orphan cleanup 배치 아직 미구현" | 실제로는 arq cron job으로 구현됨 — 정정 ✅ |
| G11 | 문서 불완전 | 구현됐으나 §4.2 endpoint 표에 없는 조회 헬퍼 6종 | §4.2 표는 "초안" 명시 + 버전 로그에 대부분 기록 — 경미, §4.2에 일괄 추가 검토(후속) |
| — | 의도된 이연 (1차 G5 유지) | `emotion-scores`/`emotion-alerts`/`publications` 엔드포인트 미구현 | 정상 — Phase 2/3, decisions #25 |

---

## G7. design §11.2 Implementation Order 스테일

- **item 1**: "schema.md **v1.11**, ... 마이그레이션 **0001~0006**" → 실제 schema.md **v1.12**, 마이그레이션 **0001~0007**(`0007_chapter_compaction.py`, PR #15).
- **item 5**: "Compaction Engine(§2.11 요약·키워드)은 **미구현**(body_text 원문 대체)" → **구현됨**(PR #15). 추가로 Critic Agent(§2.11 3단계, `questions` 생성 — PR #16)가 item 5 범위인데 미언급.
- **preamble**: "Do 단계 보안 트랙(PR #1~8)" — 세션은 PR #1~19까지 진행. 요약 bullet이라 확장.

**조치**: item 1·5·preamble을 실제 상태로 갱신(design v0.36).

## G8. design §11.1 File Structure — "Alembic 0001~0006"

`migrations/versions/` 주석이 0006까지 → 0007. **조치**: 0001~0007로 정정.

## G9. structure.md 모듈 수 스테일

실제 도메인 모듈 **12개**: `users`·`devices`·`author`·`care`·`schedule`·`sync`·`consent`·`family_members`·`invitations`·`notifications`·`photos`·`photo_requests`.

- structure.md 라인 30 트리 주석: "8개 논리 모듈 전부 구현 완료"
- structure.md §2 "Phase 1 구현 범위": "10개 논리 모듈 전부 4계층 구현 완료" — `consent`·`notifications` 빠짐
- (design.md §11의 import-linter note는 이미 "12개 도메인 모듈"로 정확)

**조치**: structure.md 두 곳을 "12개"로 정정(v1.35). `author`가 Compaction·Critic Agent도 포함함을 명시.

## G10. structure.md §2 — orphan cleanup "미구현" 스테일

"`photos`의 orphan cleanup 배치(sync-contract.md §4, 24시간 지나도 `pending_upload`인 행 정리)는 **아직 미구현**" → 실제로는 `worker.py`의 `cleanup_orphan_photos` arq cron job으로 **구현됨**(커밋 `72b212f`). **조치**: 정정.

## G11. §4.2 endpoint 표 불완전 (구현 > 문서)

구현됐으나 design §4.2 "Endpoint List(초안)" 표에 행이 없는 조회 헬퍼:

| 엔드포인트 | 소비처 | 표 등재 |
|---|---|---|
| `GET /chapters/{id}` | apps/web 자서전 뷰어 단건 | 버전 로그만 |
| `GET /chapters/{id}/revisions` | apps/web 감수 화면 이력 | 버전 로그만 |
| `GET /conversation-chunks/{id}` | (내부) | 없음 |
| `GET /schedule-items/{id}` | (조회) | 없음 |
| `POST /schedule-items/{id}/respond` | 일정 응답(확인/거절) — sync-contract §3 Device-Wins 필드 병합의 실현 | 버전 로그(0.20) |
| `GET /users/{id}/consent-state` | 온보딩 게이트 | 버전 로그(0.18) |

표에 "상세 요청/응답 스펙은 Do 단계에서 OpenAPI로 확정"이라 명시돼 있고 대부분 버전 로그 산문에 기록돼 있어 **경미**. §4.2 표를 구현과 1:1로 맞추는 것은 별도 정비(또는 OpenAPI codegen 도입 시 자동).

---

## 정상 확인 항목

| 항목 | 결과 |
|---|---|
| ruff / ruff format / mypy(161) / pytest(155) | 통과 |
| import-linter (4 contract) | **4 kept, 0 broken** (`core/auth.py` 순수화 후 예외 1건 = `model_registry`만) |
| schema.md §5 DDL ↔ 실 DB | 21개 테이블 일치. `chapters` compaction 3컬럼(v1.12, 0007) 포함 |
| 4계층·모듈 경계 규칙 | 준수 (import-linter가 CI에서 강제) |
| §2.11 서버측 클로즈드 루프 | 3단계(Critic Agent, `questions` 생성)·4단계(Compaction, 요약·키워드) 구현. 1·2단계(온디바이스 VAD/STT/SLM/TTS)는 모델 선정(#27) 대기. 5·6단계는 `sync/download` + 온디바이스 |
| apps/web·apps/admin Keycloak 로그인 | Auth.js(decisions #49), 양쪽 앱 실 flow 브라우저 검증 |
| `emotion_*`·`publications` 엔드포인트 미구현 | 정상 — Phase 2/3 (§11.2, decisions #25) |

---

## 후속 (별도 트랙)

1. **apps/web·apps/admin 공유 코드 추출** — `lib/api/client.ts`·`case.ts`·`auth.ts`·UI 컴포넌트가 두 앱에 복붙(structure.md가 "공유 패키지 없어 각자" 인정). `packages/` 공유 패키지 검토.
2. **§4.2 endpoint 표 ↔ 구현 1:1 정비** (G11) — 또는 OpenAPI codegen 도입 시 자동 해소.
3. **`POST /chapters/{id}/review` 승인 시 compaction 재계산** — 현재 `save_draft`(파이프라인) 시에만. 확정 시점 본문으로 요약 갱신하면 온디바이스가 최종본 요약을 받음.
4. **PDCA Report 갱신** — 1차 보고서(`04-report/`)는 PR #1~11 기준. #12~19 반영 필요.
