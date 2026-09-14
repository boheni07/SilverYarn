# silveryarn-platform — Do 단계 사이클 보고서

> **작성일**: 2026-09-10 (§1 최초 작성 시점 — PR #1~11 기준. §1의 지표·서술은 그 시점 스냅샷으로 남겨두고, #12 이후 확장분은 아래 **§3-2**·**§3-3**·**§3-4**·부록에 이어 적었다)
> **갱신일**: 2026-09-11 — PR #12~24 반영 → 2026-09-13 재갱신 — PR #25~42 반영, §3-3 신설 → **2026-09-14 재갱신 — PR #43~50 반영, §3-4 신설**
> **대상 사이클**: CTO 착수 심사(`docs/02-design/cto-review-2026-09-05.md`) 보안 블로커 해소 + Design v0.6→v0.58 잔여 구현 + 법무·인프라·경영 미결 14건 전체 확정·구현 + Do 단계 후속(출판 파이프라인·모바일 UI 전면 개편·웹 실 인증 세션 연결)
> **PR 범위**: #1 ~ #50 (전부 main squash 머지, #38 결번)
> **PDCA 위치**: Do 진행 중 → Check 2회(`docs/03-check/gap-analysis-2026-09-10.md`, `-11.md`) → 본 Report(3차 갱신). **[`blocked-decisions-tracker.md`](../../03-check/blocked-decisions-tracker.md)의 법무 6건·인프라 5건·경영 3건(14건 전체)이 2026-09-13 PR #39로 전부 확정+구현 완료** — 이 사이클이 추적하던 외부 회신 대기 항목은 더 이상 없다(§5 갱신 참조). 그 이후에도 Do 단계는 계속 진행 중(§3-4) — 남은 후속은 실측 성격의 온디바이스 SLM 벤치마크(§3-3, §7, 실기기 확보 대기)와 미착수 화면 1건(모바일 사진 화면, §7)뿐

---

## 1. 개요

CTO팀 착수 심사(2026-09-05, 7개 관점 전원 "Go with Conditions")에서 **보안 관점 법적 블로커 6건(B1~B6)** 이 "Do 단계 이연 불가"로 지목됐다. 이 사이클은 그 6건 중 **코드로 닫을 수 있는 부분을 전부 구현**하고, 병행해서 Design 문서의 미구현 잔여분(온보딩 흐름 §2.9, 모듈 경계 강제 §11, 동기화 멱등성)을 채웠다.

**결과 요약**:

| 지표 | 값 |
|---|---|
| 머지된 PR | 11건 (#1~#11), 전부 CI 그린 + squash |
| 마이그레이션 | 0002~0006 신규 (0001 위) |
| 백엔드 도메인 모듈 | 12개 (4계층 전부) |
| 백엔드 단위 테스트 | 145 |
| 실 인프라 e2e | `e2e_pii_auth_check` 17/17 · `e2e_http_smoke` 13/13 · `e2e_keycloak_check` 9/9 |
| CI 게이트 | ruff · ruff format · mypy(160 파일) · pytest · **import-linter(4 contract)** · apps/web·admin lint/build · apps/mobile ktlint/test/assembleDebug |
| Design 문서 | v0.6 → **v0.29** |

---

## 2. 계획 대비 실적 — CTO 보안 블로커 B1~B6

| 블로커 | 계획(심사 지적) | 실적 | 상태 |
|---|---|---|---|
| **B1** 정서 데이터는 "기록" 시점부터 위법 소지 | 정서 파이프라인 OFF, 알림 수신은 opt-in | 정서 파이프라인 피처플래그 OFF(decisions #25), `emotion_scores`/`emotion_alerts` 엔드포인트 미구현. `notification_settings.receives_emotion_alerts` 기본값 **opt-out(false)** + `(family_member_id, channel)` UNIQUE (PR #3, 마이그레이션 0005) | ✅ 코드분 완료 / ✅ **법적 분류 확정**(2026-09-12, decisions #52/#55 — 일반 개인정보로 충분, "진단" 표현 회피). 기능 자체는 여전히 Phase 1 피처플래그 OFF(제품 판단), "발송 임계치" 세부 로직만 별도 대기(decisions #19) |
| **B2** 대리동의 법적 근거 공백 | 동의 주체(self/proxy/legal_guardian) 구분 | `consent` 모듈 신규(PR #1). `ConsentLog.actor`(self/proxy)를 `granted_by` 유무에서 파생. 온보딩이 `recordConsent(data_collection)` 호출 | ✅ **완료**(2026-09-12, decisions #53) — 가족(1촌 이내) 대리동의를 유효로 확정. 명시적 enum(`legal_guardian`)은 여전히 미도입이나 YAGNI 판단(actor는 파생값으로 충분). `apps/web` `/consent` 대리 동의 관리 화면(PR #33) |
| **B3** 보유기간·파기정책이 전 문서에 없음 | `retention_until`/`purged_at` + 파기 오케스트레이션 | **crypto-shredding 수단 확보**: 사용자 파기 = `user_encryption_keys` 행 삭제 → 그 사용자 PII 자유텍스트·contact·birth_date 전량 복호화 불가 (PR #1/#4). `e2e_pii_auth_check`가 실제로 검증 | ✅ **완료**(2026-09-13, decisions #56, PR #39) — crypto-shredding을 파기 수단으로 정식 채택. Postgres cascade가 이미 4개 저장소 중 3개(PG 자체+DEK)를 커버함을 재조사로 확인, 남은 Qdrant/Neo4j/MinIO는 `UserErasureService`가 오케스트레이션. 시간기반 보유기간은 `conversation_chunks` 원문에 한정(`retention_policies`+`RetentionPurgeService`) |
| **B4** PII 암호화 방식 미결 = 스키마 결정, 이연 불가 | 애플리케이션 레벨 필드 암호화 + 사용자별 DEK | **완료**. `core/crypto.py` — Fernet(AES-128-CBC+HMAC), 사용자별 DEK를 `PII_KEK`로 랩핑(`user_encryption_keys`), `pii.v1.` 토큰 접두. 1차(PR #1): `chapters.body_text`·`chapter_revisions.body_text_snapshot`·`conversation_chunks.{transcript_on_device,transcript_server,assistant_response}`. 2차(PR #4): `family_members.contact`·`invitations.contact`(암호문 + `contact_bidx` HMAC 동등검색), `users.birth_date`(DATE→VARCHAR 암호문). `name`은 평문 확정 | ✅ 완료 / ✅ **3차 중 blind index 분리 완료**(2026-09-12, decisions #60, PR #32 — `BLIND_INDEX_KEY` 정식 분리). `PII_KEK` 자체의 Vault transit 이전은 시크릿 매니저 인프라 선결 필요로 계속 보류 |
| **B5** 인증/인가/테넌시/감사모델 구조적 공백 | Keycloak 실검증, RBAC/IDOR, 감사로그, 테넌시 | **대부분 완료**. Keycloak JWKS RS256 검증 + `sub`→`family_members.keycloak_sub` 매핑(PR #1). Device Token = `device_credentials` SHA-256(PR #1). `authorize_user_access(principal, user_id, roles, require_2fa)` RBAC + IDOR 방지 — 13개 라우터 적용(PR #1/#2). 초대 수락→계정 연결(PR #2). social_worker fail-closed(PR #5). `access_logs` HTTP 미들웨어 감사로그(PR #1). 무인증 401(≠500) 버그 수정(PR #7). 로컬 Keycloak realm + e2e(PR #8) | ✅ 인증·인가·감사 완료 / ✅ **social_worker 조건부 재포함**(2026-09-13, decisions #54, PR #34 — `third_party_access` 동의 게이트) / ✅ **`organizations` B2G 시설 테넌시 완료**(2026-09-13, decisions #59, PR #37 — 안전망 스코프로 착수, 정식 B2G 대량열람 모델은 계속 스코프 밖) |
| **B6** Zero External Data Egress가 설계 내부와 충돌 | egress 범위 정의 + 통제 | 벡터 payload에 원문 미저장 원칙은 `upload_pipeline_service`에서 준수(payload=`user_id`만). egress 범위 정의·네트워크 통제는 인프라 설계 과제 | ✅ **완료**(2026-09-13, decisions #58 + [`data-classification-policy.md`](../../02-design/data-classification-policy.md) 신규) — PII/원본데이터 vs 메타데이터 4단계(Tier 1~4) 경계 명문화. self-hosted 관측 스택(PR #36)도 이 원칙 위에서 구축(SaaS APM 배제) |

---

## 3. 계획 대비 실적 — Design 문서 잔여 구현

| 항목 | 실적 | PR |
|---|---|---|
| 동기화 계약 잔여 — 업로드 멱등성 | arq `_job_id` + 파이프라인 사전 확인 + `uq_conversation_chunks_turn` 부분 유니크 인덱스 3계층 (sync-contract §2.3, 마이그레이션 0004) | #1 |
| `notifications` 모듈 (WF5 알림 설정) | `GET/PUT /family-members/{id}/notification-settings` | #3 |
| §2.9 온보딩 흐름 — 서버 3연쇄 | `OnboardingCoordinator`: createUser → POST /devices → recordConsent. 상태 호이스팅(sealed `OnboardingStep`, nav/ViewModel 미도입 확정) | #6 |
| §2.9 온보딩 흐름 — 앱 시작 게이트 | `AppEntry.kt`: `device_state.device_id`로 재시작 스킵. `FirstSyncScreen`(최초 Wi-Fi 동기화). `KioskController`(install_mode="kiosk" → lockTask). `SyncRunner`(SyncWorker에서 분리) | #10 |
| §11 모듈 경계 CI 강제 (CTO Enterprise B3) | `import-linter` contract 4개 + CI `lint-imports` 스텝 | #11 |
| PDCA Check | `docs/03-check/gap-analysis-2026-09-10.md` — 문서 드리프트 4건 수정, 결함 1건(`photo_requests/__init__.py` 누락) 수정 | #9 |

---

## 3-2. 2차 확장 — PR #12~24 (갱신일 2026-09-11)

Check #1 이후 이 사이클을 종료하지 않고 이어서 §2.11 서버측 클로즈드 루프 완성, 웹 콘솔 실 인증, 공유 코드 정리, 웹·모바일 남은 화면 셸까지 계속 진행했다. CTO 블로커 B1~B6 자체는 §2의 상태에서 변화가 없다(전부 외부 회신 대기) — 아래는 그 대기 기간에 계속 진행 가능했던 코드 작업이다.

| 영역 | 실적 | PR |
|---|---|---|
| 아키텍처 정리 | `core/auth.py` 순수화 — 토큰 검증·인가 규칙·조회 포트 Protocol만 남기고, 리포지토리 조립 FastAPI 의존성은 신규 `core_service/auth_deps.py`(composition root)로 분리. import-linter contract ④ 예외 3→1건(`model_registry`만) | #13 |
| 문서 인프라 | 법무·인프라 결정 대기 트래커(`blocked-decisions-tracker.md`) 신설 — 회신을 채워가며 관리하는 살아있는 문서 | #14 |
| §2.11 서버측 클로즈드 루프 | **4단계 Compaction Engine**: `LLMClient.compact_chapter`(vLLM) + `ChapterService.compact_chapter`(stale 판정) + 파이프라인 best-effort 호출, `chapters.compaction_*`(마이그레이션 0007). `sync/download`가 body_text 원문 대신 요약을 내려보냄 | #15 |
| §2.11 서버측 클로즈드 루프 | **3단계 Critic Agent**: `questions` 큐에 생성 경로 신설(이전 read-only) — `LLMClient.critique_and_generate_questions`(Fact/Emotion/Relation/Reflection 4축) + `QuestionService.generate_followups`(큐 8개 상한·중복 제거) | #16 |
| apps/web | 알림 수신 설정 화면(`(family)/notification-settings`) — `notifications` 모듈 첫 웹 소비자 | #17 |
| apps/web·admin 실 인증 | **Auth.js(NextAuth v5) + Keycloak 로그인**(decisions #49) — `silveryarn-web` public client + PKCE, `lib/api/client.ts` server-only + `auth()` 토큰 주입, Next.js 16 `proxy.ts`가 미로그인 요청을 `/login`으로. web은 Server Action 경유, admin은 GET 전용이라 불필요. 양쪽 앱 실 flow 브라우저 검증 | #18, #19 |
| PDCA Check #2 | `gap-analysis-2026-09-11.md` — PR #10~19 반영한 설계문서 스테일 5건(G7~G11) 정정 | #20 |
| 아키텍처 정리 | **npm 워크스페이스 + `packages/web-shared`**(decisions #50) — apps/web·admin에 복제돼 있던 Auth.js 설정·API 클라이언트·UI 프리미티브를 단일 공유 패키지로 통합. CI 왕복 2회로 lockfile 함정 2건 발견·수정(§6 L7·L8) | #21 |
| apps/web | **가족 대시보드 "오늘의 기억 리포트"**(WF1) — 오늘 대화 수(신규 PII-비노출 COUNT 엔드포인트)·오늘 새 회고 수·Compaction 요약 카드. "정서 상태"·"정서 추이 차트"는 렌더하지 않고 파이프라인 OFF 사실을 안내(decisions #25 준수) | #22 |
| apps/mobile | **홈 셸(M2) + 하단 탭 4개** — `AppEntry.kt`가 임시로 띄우던 `AssistantHomeScreen`을 실제 `AppShell`로 교체. 통계는 전부 로컬 DB 집계(오프라인 완결). 마이크 세션은 SLM 의도 라우터 스텁이라 말벗돌봄 모드 고정 | #23 |
| services/backend | 챕터 감수 승인 시 Compaction 재확인 안전망(gap-analysis G11 후속 #3) — 직전 압축이 vLLM 장애로 실패했을 때만 확정 시점에 재시도 | #24 |

**§1 지표 갱신(2026-09-11 기준)**: 머지된 PR **24건**(#1~#24) · 마이그레이션 0002~**0007** · 백엔드 단위 테스트 **156** · Design 문서 v0.6 → **v0.39** · decisions.md → **v0.21** · mobile-schema.md → **v0.10**. import-linter 4 contract는 계속 4 kept·0 broken.

---

## 3-3. 3차 확장 — PR #25~42, 법무·인프라·경영 14건 전체 확정+구현 완료 (갱신일 2026-09-13)

§3-2까지는 CTO 블로커 B1~B6가 전부 "외부 회신 대기"였다. 이 구간에서 그 구도가 완전히 바뀌었다 —
**사용자가 "결정이 필요한 항목을 하나씩 대화하면서 결정해나가자"고 요청**해, `blocked-decisions-tracker.md`가
추적하던 법무 6건(Q1~Q6)·인프라 5건(I1~I5)·경영 3건 **14건 전체를 일괄 확정**(decisions.md #52~#65,
PR #31, 순수 문서)한 뒤, 그 결정들을 작은 것부터 순서대로 전부 구현했다. **PR #39로 14건 전체 구현 완료**
— §2 표의 B1~B6 상태 열이 이를 반영한다.

| 영역 | 실적 | 관련 decisions | PR |
|---|---|---|---|
| 문서 정비 | 결정 대기 트래커 완료 항목 갱신(첫 가족 연결·페르소나 룰셋) | #51 | #29 |
| 실측 준비 | 온디바이스 SLM 벤치마크 프로토콜 + 측정 하니스(`ondevice-slm-benchmark-protocol.md`, `apps/mobile/.../benchmark/`) — 실기기 없어 실측 자체는 미실행 | #27/#9/#31 | #30 |
| **법무·인프라·경영 14건 일괄 확정** | Q1~Q6(법무, 잠정 회사정책 명시)·I1~I5(인프라)·경영 3건을 AskUserQuestion으로 순서대로 결정, decisions.md §2.9 신설 | #52~#65 | #31 |
| PII 3차 | blind index 키를 `PII_KEK`에서 `BLIND_INDEX_KEY`로 정식 분리, `scripts/backfill_blind_index.py` | #60 | #32 |
| 동의 UX | 가족 대리 동의 관리 화면(`apps/web` `/consent`) — 백엔드는 이미 `granted_by` 지원 중이었음을 재발견 | #53 | #33 |
| 인가 확장 | 복지사(social_worker) `third_party_access` 동의 게이트 — `auth_deps.authorize_elder_data_read()` 신규, 10개 엔드포인트 전환, 실 인프라 e2e 11/11 | #54 | #34 |
| 동의 UX | 국외이전(FCM) 고지·동의 UI — 모바일 온보딩에 별도 체크박스(기본 미동의) | #57 | #35 |
| 관측성 | self-hosted GlitchTip+Prometheus+Grafana+Loki, `glitchtip-bootstrap` 자동화. 부수 발견: `handle_unexpected`가 예외를 완전히 삼키던 버그 수정 | #61 | #36 |
| 테넌시 | B2G 시설(`organizations`) 안전망 — `ElderAccessContext`로 `auth_deps.py` 리팩터링, apps/admin 시설 관리 화면 | #59 | #37 |
| **보유기간·계정삭제** | crypto-shredding + `UserErasureService`(Qdrant/Neo4j/MinIO) + `RetentionPurgeService` + admin UI — **14건 중 마지막 항목**. 부수 발견: `VECTORDB_API_KEY=""` https 오판정 버그 수정 | #56 | #39 |
| 문서 동기화 | design.md §3/§4.2/§5.1/§7/§9/§11 드리프트 정정(실행 중 OpenAPI와 전수 대조), 신규 `data-classification-policy.md`(I1 후속), glossary.md 용어 8건 추가, 양쪽 `_INDEX.md`·CLAUDE.md 정정 | #58 | #40 |
| 사업비 산정 | IFPUG FP 기반 SW개발비 산정 내역서(정통법·간이법 2종) — 서버 API 46종+저장소 23종, 모바일 기능 13종+저장소 6종 전수 산정 | — | #41, #42 |

**§1 지표 재갱신(2026-09-13 기준)**: 머지된 PR **41건**(#1~#42, #38 결번) · 마이그레이션 0002~**0012** · 백엔드 단위 테스트 **212** · Design 문서 v0.6 → **v0.52** · decisions.md → **v0.25** · schema.md → **v1.17**(도메인 19+부속 4) · workflow-diagrams.md → **v0.6**(21종, §21 신규) · glossary.md → **v1.2**. import-linter 4 contract는 계속 4 kept·0 broken.

---

## 3-4. 4차 확장 — PR #43~50, 법무·인프라·경영 14건 완료 이후 Do 단계 후속 (갱신일 2026-09-14)

법무·인프라·경영 14건(§3-3)이 끝난 뒤에도 사이클을 종료하지 않고, "다음 사이클 진행해줘" 반복 요청에 매번
report.md 권고(§7)·design-validator·사용자 직접 요청을 근거로 계속 진행했다. 이 구간의 특징은 **문서
정합성 점검을 3회(PR #40/#43/#48) 반복**했다는 것 — 매번 큰 기능 PR 뒤에 실제 드리프트가 발견됐다(패턴은
§6 L9 참조). 또한 페르소나가 "은빛이"에서 **"은실이"**로 재명명되고(decisions #66), 모바일 UI가 하단
탭 방식에서 **대화 전용 단일 화면**으로 전면 개편됐다(decisions #66~#68) — 둘 다 사용자가 세션 중
직접 결정한 사항이다.

| 영역 | 실적 | 관련 decisions | PR |
|---|---|---|---|
| 문서 정비 | `docs/presentations/.bkit/`(2026-09-06부터 방치된 고아 디렉터리) 삭제, structure.md 변경이력 표 재정렬(v1.22 이후 날짜순 뒤섞임 발견), report.md의 CTO 블로커 상태표가 "법무 회신 대기"로 정정 안 된 채 남아있던 것 수정 | — | #43 |
| **출판 파이프라인** | Phase 3 출판/인쇄 파이프라인(design.md §2.6) — 신규 `publications` 모듈(15번째 도메인 모듈), 전체 챕터 confirmed 검증 → arq 비동기 잡 → reportlab(PDF, 한글 Adobe 표준 CJK CID 폰트)·EbookLib(ePub) 실 조판 → 전용 MinIO 버킷 → presigned 다운로드. apps/web `(family)/publications` 신규 | — | #44 |
| 말벗돌봄 대화 | 대화 화면·세션·mock STT/SLM 최초 구현(`ConversationSessionController`, `MockSttEngine`/`MockSlmEngine`) — 이후 PR #47에서 UI가 전면 개편되며 대화 엔진 자체는 그대로 이어받음 | — | #45 |
| 화면설계서 | UI/UX 관점 전용 신규 문서 `docs/02-design/screen-definitions.md` — 실제 구현 코드를 SoR로 모바일·웹 사용자·웹 관리자 전 화면(당시 27개)을 목적·구성요소·구현상태(✅완료/🟡mock/⬜스텁/⚠️임시방편/🔒비활성) 뱃지로 전수 정의 | — | #46 |
| **모바일 UI 전면 개편** | "은실이" 대화 전용 UI(사용자 요청, decisions #66~#68) — 하단 4탭·화면 4종 완전 제거, `presentation/companion/` 패키지 하나로 통합. 신규 실 VAD(`AmplitudeVoiceActivityDetector`, 진폭 임계값 기반) — 버튼 클릭과 자연스러운 발화 둘 다 같은 파이프라인으로 수렴. 페르소나명 "은빛이"→"은실이" 재명명, 자서전 작가·비서 모드까지 하나의 대화 안에서 통합 | #66~#68 | #47 |
| 문서 정합성 2차 | PR #47 반영 누락분 정정 — "은빛이" 잔존 표기 8곳, structure.md 모바일 폴더 트리 드리프트(삭제된 `presentation/{author,care,assistant}` 계속 서술), `_INDEX.md` 버전 참조 재동기화(structure.md가 **6버전** 밀려 있던 것이 최대 발견) | — | #48 |
| **웹 실 인증 세션 연결** | 신규 `GET /me` — `require_auth`가 이미 계산해 두던 `AuthContext.memberships`를 그대로 직렬화(새 도메인/서비스 로직 0). apps/web 9개 화면이 `?userId=` 수동 입력 대신 `?elder=`+`resolveCurrentUserId()`로 전환, W-02(임시 홈)를 세션 자동 연결 홈으로 재정의, notification-settings·consent의 "구성원 먼저 선택" 단계도 `resolveCurrentMembership()`으로 제거. apps/admin은 조사 결과 대상이 아님을 확인(role 기반 전체 열람) | #69 | #49 |
| 발표자료 | 설계발표 PPT 신규(사용자 요청 — 시스템 흐름 이해 중심 재구성) — 44슬라이드, 전체 컴포넌트 다이어그램·Closed-Loop·마스터 업무흐름도(Swimlane)·ERD를 전부 네이티브 PPT 도형으로 시각화, 단위 시스템별 상세 흐름 13종 + UI/UX 실 구현 화면 목업. PowerPoint COM으로 전체 렌더링해 육안 검증(§6 L10) | — | #50 |

**§1 지표 재갱신(2026-09-14 기준)**: 머지된 PR **49건**(#1~#50, #38 결번) · 마이그레이션 0002~**0012**(변경 없음) · 백엔드 단위 테스트 **223** · Design 문서 v0.6 → **v0.58** · decisions.md → **v0.27**(§2.10~§2.11 신설, #66~#69) · screen-definitions.md → **v0.3**(신규, 24개 화면) · workflow-diagrams.md → **v0.7** · schema.md → **v1.18** · glossary.md → **v1.3** · structure.md → **v1.41**. import-linter 4 contract는 계속 4 kept·0 broken.

---

## 4. 검증

### 실 인프라 e2e (Docker: postgres·redis·qdrant·neo4j·minio·keycloak, 마이그레이션 0006)

| 스크립트 | 결과 | 커버리지 |
|---|---|---|
| `scripts/e2e_pii_auth_check.py` | **17/17** | repository 레이어 — 암호문 `pii.v1.` 접두 확인, `user_encryption_keys` 행, body_text/스냅샷 라운드트립, `contact_bidx` HMAC, conversation_chunk 멱등성(`c1.id == c2.id`, 1행), **crypto-shredding**(키 삭제 → 복호화 시 `RuntimeError`) |
| `scripts/e2e_http_smoke.py` | **13/13** | HTTP 레이어 — `POST /users`·`/devices`(device_token), consent 무인증 401, X-Device-Token 201, IDOR 403(토큰≠device_id), `access_logs` 미들웨어 적재 확인 |
| `scripts/e2e_keycloak_check.py` | **9/9** | JWKS RS256, `sub`→family_members 매핑, `authorize_user_access` RBAC, social_worker fail-closed 403, unlinked 403, 2FA(`amr`) 게이트 → 챕터 검토 200, admin-only 403 |

### CI (GitHub Actions, `.github/workflows/ci.yml`)

4 job — `services/backend`(ruff·format·mypy·**import-linter**·pytest), `apps/web`·`apps/admin`(lint·type-check·build), `apps/mobile`(ktlintCheck·test·assembleDebug). PR #1~#11 전부 그린.

---

## 5. 미해결 / 다음 사이클 이월

> §1~4는 PR #1~11 시점 기준, §3-2는 #12~24, §3-3은 #25~42, §3-4는 #43~50까지 갱신했다. 상세·회신 관리는
> **[`docs/03-check/blocked-decisions-tracker.md`](../../03-check/blocked-decisions-tracker.md)** (살아있는 트래커).

### 외부 결정 대기 — 2026-09-13 기준 전부 해소됨

> 아래는 §3-2 시점(2026-09-11)까지 "외부 회신 대기"였던 항목의 **당시 스냅샷**이다. 이 사이클(§3-3,
> PR #31~#39)에서 **7건 전부 사용자 결정으로 확정되고 코드까지 구현 완료**됐다 — 더 이상 유효한
> "대기 목록"이 아니라 이력으로 남긴다. 각 행의 현재 상태는 §2 표(B1~B6) 갱신분 참조.

| 항목(당시 표현) | 블로커 | 당시 대기 대상 | 현재 상태 |
|---|---|---|---|
| 보유기간 수치 + 5개 저장소 통합 파기 오케스트레이션 | B3 | ⚖️ 법무 — 보유기간·crypto-shredding 인정 여부 | ✅ 완료(decisions #56, PR #39) |
| 정서 모니터링 알림 법적/윤리 기준 | B1 | ⚖️ 법무·윤리 (Phase 2) | ✅ 법적 분류 확정(decisions #52/#55) — 발송 임계치 세부만 잔존(#19) |
| 대리동의 `legal_guardian` enum + `data_subject` RBAC | B2 | ⚖️ 법무 — 성년후견 대리동의 근거 (decisions #12) | ✅ 완료(decisions #53, PR #33) — enum 자체는 YAGNI로 미도입 |
| social_worker 어르신 데이터 재포함 | B5 | ⚖️ 법무 — 제3자제공 여부 + 전용 consent 유형 (decisions #48) | ✅ 완료(decisions #54, PR #34) |
| `organizations` B2G 시설 테넌시 | B5 | 📋 B2G 운영모델 | ✅ 완료(decisions #59, PR #37, 안전망 스코프) |
| Zero Egress 범위 정의 + 네트워크 통제 | B6 | 🏗️ infra-architect | ✅ 완료(decisions #58, `data-classification-policy.md`, PR #40) |
| `PII_KEK` Vault transit 이전 + blind index 키 분리 | B4 3차 | 🏗️ 시크릿 매니저 인프라 | 🟡 blind index 분리만 완료(decisions #60, PR #32) — Vault 이전 자체는 시크릿 매니저 인프라 선결 필요로 계속 보류 |

**남은 후속(외부 회신 대기 아님, 별도 실측 트랙)**: 온디바이스 SLM 모델 선정·"최근 5일" 캐시 기준·실시간
파이프라인 수치(decisions #27/#9/#31) — 프로토콜+하니스 준비 완료(PR #30), 물리 안드로이드 기기 확보가
유일한 선결조건.

### 코드 후속 (착수 가능, 우선순위 낮음)

- ~~`core/auth.py` → 모듈 infrastructure 결합 제거~~ — **완료 (PR #13)**. `core/auth.py`는 순수(토큰 검증·인가 규칙·조회 포트 `FamilyMemberDirectory`/`DeviceTokenDirectory` Protocol), 리포지토리 조립은 `core_service/auth_deps.py`(composition root). import-linter contract ④의 예외가 3건 → 1건(`model_registry`만).
- ~~Compaction Engine (design §2.11)~~ — **요약·키워드 부분 완료 (PR #15, 감수 승인 시 재확인 안전망은 PR #24)**: `LLMClient.compact_chapter`(vLLM) + 업로드 파이프라인 best-effort 호출 + `chapters.compaction_*`(마이그레이션 0007). `sync/download`가 요약을 내려보냄(vLLM 미가동 시 `body_text` 앞 200자). **미구현**: "단기 압축 기억 JSON 룰셋"(페르소나, §2.10 연동) — 온디바이스 SLM/페르소나 배포 경로 확정 후.
- ~~apps/web·admin 공유 코드 추출~~ — **완료 (PR #21)**. npm 워크스페이스 + `packages/web-shared`(decisions #50).
- ~~웹 가족 대시보드 "오늘의 기억 리포트"~~ — **완료 (PR #22)**.
- ~~모바일 홈 셸(M2) + 하단 탭 4개~~ — **완료 (PR #23)**.
- ~~§4.2 endpoint 표 ↔ 구현 1:1 정비~~ — **완료 (PR #26, design.md v0.40)**. OpenAPI 스키마 전수 대조로 실제 갭이 G11이 지목한 6건보다 컸음을 확인(17행 추가 — `family-members` 목록/생성 전체 누락 등).
- ~~첫 가족 구성원 연결 경로~~ — **완료 (PR #28, decisions #51)**. 사용자 결정: admin 중개 경로. apps/admin `(admin)/family-members`(첫 쓰기 화면) + apps/web `/invitations/[token]`(수락). **모바일 화면은 필요 없었음** — device-token 부트스트랩 안을 채택하지 않아 모바일 쪽 변경 자체가 없다.
- ~~온디바이스 SLM 의도 라우터 (workflow-diagrams.md §19) — 마이크 세션이 말벗돌봄 모드로 고정된 문제~~ — **PR #47로 재해결**: 모드 고정 자체가 사라졌다. "은실이" 대화 전용 UI 개편으로 자서전 작가·말벗돌봄·비서 3모드가 화면 분리 없이 하나의 대화로 통합됐고, `ConversationSessionController`가 턴마다 응답 키워드로 `author`/`care` 기록 모드를 동적 판정한다. 다만 이 라우팅은 여전히 `MockSlmEngine`의 얕은 키워드 매칭 — 실 SLM 붙으면 의도분류 로직 자체는 보강 필요.
- 온디바이스 STT/SLM/TTS 런타임 — 모델 선정(decisions #27, 실기기 벤치마크) 대기. VAD만 임시로 실구현됨(`AmplitudeVoiceActivityDetector`, PR #47, decisions #68).

---

## 6. 교훈 (Lessons Learned)

| # | 교훈 | 근거 |
|---|---|---|
| L1 | **실 인프라 e2e가 아니면 안 잡히는 버그가 있다** — 무인증 요청이 401 대신 500(verifier를 인자 평가 순서상 먼저 생성), FK 문자열 참조 해석 실패(`model_registry` 없이 워커가 부분 import), naive datetime 12개 파일. CI의 Fake repository 단위 테스트는 이걸 못 잡는다. | PR #7, structure.md v1.11 |
| L2 | **암묵적 namespace 패키지는 조용히 도구를 무력화한다** — `modules/photo_requests/__init__.py` 누락으로 런타임 import는 되지만 grimp/import-linter가 패키지를 아예 못 봤다. import-linter 도입이 아니었으면 계속 숨어 있었을 결함. | PR #11, gap-analysis G6 |
| L3 | **설계문서는 구현이 앞서가면 드리프트한다** — design §9.1/§11.1이 미구현 `services/{engine}/` 6-서비스 트리를 6개 PR 뒤에도 서술 중이었다. SoR 원칙 1(코드 우선)을 매 PR이 아니라 사이클 끝 Check에서야 적용. | PR #9, gap-analysis G1 |
| L4 | **법적 미결을 코드로 밀어넣지 않는 절제가 유효했다** — social_worker fail-closed, 정서 파이프라인 OFF, 대리동의 enum 미도입. "지금 안 하는 것"을 decisions.md에 근거와 함께 남겨 나중에 다시 열 수 있게 함. | PR #3/#5, decisions #12/#25/#48 |
| L5 | **모바일 CI는 로컬 사전 검증이 필수** — 이 세션 환경에 Android SDK가 없어, IntelliJ 번들 JBR + ktlint CLI로 파싱·포맷을 먼저 돌리고 푸시하는 방식으로 CI 왕복을 줄였다. KDoc 안 `/*` 시퀀스가 블록 주석 중첩 규칙과 충돌하는 함정 등. | structure.md v1.23, 메모리 `mobile-local-ktlint-verification` |
| L6 | **세션 중 사고 1건** — 포트 8000 정리 중 `taskkill`로 Docker Desktop 백엔드 프로세스를 죽여 infra 컨테이너 전부 다운. 이후 포트 프로세스는 식별 후에만 종료. | (세션 로그) |
| L7 | **npm 워크스페이스로 전환하면 플랫폼별 네이티브 바이너리가 lockfile에서 조용히 빠질 수 있다** — 기존 win32 `node_modules` 위에 증분 `npm install`을 돌리자 lightningcss/@tailwindcss/oxide의 비호스트(linux-x64-gnu 등) optional dependency가 lockfile에서 pruning됐다. `npm ci`는 로컬에서 통과하지만 CI(Linux)의 `next build`가 "Cannot find lightningcss.linux-x64-gnu.node"로 실패 — `node_modules`+lockfile을 완전히 지우고 처음부터 재설치해야 전 플랫폼 바이너리가 복원된다. | PR #21, CI 왕복 2회 |
| L8 | **Keycloak 테스트 유저는 firstName/lastName 없이 만들면 direct grant가 거부된다** — Admin REST로 만든 유저에 `requiredActions: []`를 명시해도, realm User Profile이 요구하는 `firstName`/`lastName`이 없으면 password grant가 "Account is not fully set up"(400)으로 실패한다. e2e 스크립트들은 이미 이 필드를 채우고 있었지만, 새 검증 스크립트를 짤 때 빠뜨려 재발했다. | PR #24 실 인프라 검증 |
| L9 | **큰 기능 PR 뒤엔 항상 문서 드리프트가 남는다 — 특히 버전 헤더와 폴더 트리** — "정합성 점검"을 세션 중 3번(PR #40/#43/#48) 반복했고 매번 실제 드리프트를 발견했다. 가장 흔한 두 지점: ① `_INDEX.md`의 각 문서 버전 표기(structure.md가 한때 6버전 밀려 있었음), ② 구조 문서가 실제 패키지 구조를 텍스트 트리로 하드코딩한 부분(모바일 폴더 개편 후 갱신 누락). 큰 PR 머지 직후엔 이 두 곳부터 확인하면 점검 시간이 준다. | PR #40, #43, #48 |
| L10 | **LibreOffice 없는 환경에서도 PPT를 실제로 렌더링해 육안 검증할 수 있다** — Windows에 설치된 PowerPoint를 `pywin32`(`win32com.client.Dispatch('PowerPoint.Application')`)로 열어 `Presentation.SaveAs(dir, 18)`(ppSaveAsPNG)를 호출하면 전체 슬라이드가 PNG로 내보내진다. 이 검증으로 좌표 계산 버그(엉뚱한 박스를 가리키던 연결선) 1건을 실제로 찾아 고쳤다 — python-pptx는 예외 없이 저장돼도 시각적으로는 틀릴 수 있다. | PR #50 |
| L11 | **Jetpack Compose의 "스코프 암시적 리시버 멤버"와 "평범한 top-level 확장함수"는 반대로 다뤄야 한다** — `Modifier.weight()`/`align()`은 `ColumnScope`/`RowScope`/`BoxScope`의 멤버 확장이라 명시적 import하면 오히려 컴파일 에러가 난다. 반면 `InfiniteTransition.animateFloat()`은 평범한 top-level 확장함수라 명시적 `import`가 반드시 필요하다 — 이 둘을 헷갈려 같은 PR에서 CI가 2연속 실패했다(처음엔 Gradle 의존성 자체를 잘못 의심). | PR #47 |
| L12 | **import-linter 콘솔 스크립트가 PATH에 없으면 설치 경로의 `.exe`를 직접 호출한다** — 이 환경은 venv가 없어 `lint-imports`가 bash PATH에 노출되지 않는다. `pip show import-linter`로 설치는 확인되지만 `python -m importlinter`류의 모듈 진입점도 없다 — 실제로는 `.../Python314/Scripts/lint-imports.exe`가 그대로 존재하므로 절대경로로 직접 실행하면 정상 동작한다. | PR #49 |

---

## 7. 다음 사이클 권고

> 2026-09-13 갱신: 아래 1·2번 권고는 **§3-3(PR #31~#40)에서 전부 실행되고 완료됐다**. 원문은
> 이력으로 남기고, 완료 표시만 추가한다. → **2026-09-14 재갱신**: §3-4(PR #43~50) 반영, 3번 재확인
> 결과와 신규 권고 4~6번 추가.

1. ~~**법무 회신 취합** — B1(정서)·B2(대리동의)·B3(보유기간)·B5(제3자제공)가 한 묶음. 회신이 오면 retention 정책 + 파기 오케스트레이션이 가장 큰 단일 작업.~~ — **완료**. 사용자가 직접 결정 대화를 요청해 14건 일괄 확정(decisions #52~#65, PR #31) 후 전부 구현(PR #32~#39).
2. ~~**infra-architect 착수** — B6(egress), `organizations` 테넌시, `PII_KEK` Vault, GPU 토폴로지, 관측 스택(self-hosted).~~ — **대부분 완료**: egress 경계 문서화(PR #40), organizations 테넌시(PR #37), 관측 스택(PR #36). `PII_KEK` Vault 이전과 GPU 토폴로지(VRAM 예산표)만 계속 보류(각각 시크릿 매니저 인프라, 실기기 벤치마크 선결).
3. **온디바이스 SLM 모델 선정 벤치마크**(decisions #27, 실기기) — §19 의도 라우터는 PR #47로 이미 재해결됐고(모드 고정 자체가 사라짐, 코드 후속 절 참조), §2.10 페르소나 JSON 룰셋도 온디바이스 소비까지 PR #47에서 연결됐다 — 남은 건 순수하게 실 STT/SLM/TTS 엔진 자체뿐. **2026-09-14 재확인**: 이 세션 환경에 `adb`/`emulator`/`ANDROID_HOME`이 전혀 없어 여전히 착수 불가능 — 계속 다음 사이클 최우선 권고(실기기 확보가 유일한 선결조건).
4. (완료) ~~`core/auth.py` 포트 리팩터링~~ → PR #13. ~~apps/web·admin 공유 코드 추출~~ → PR #21. ~~§4.2 endpoint 표 정비~~ → PR #26. ~~법무·인프라·경영 14건~~ → PR #31~#39. ~~Phase 3 출판 파이프라인~~ → PR #44. ~~모바일 UI 전면 개편~~ → PR #47(decisions #66~#68). ~~웹 `?userId=` 임시 패턴 제거~~ → PR #49(decisions #69).
5. **모바일 사진 화면 신규** — report.md 이전 갱신부터 계속 후보로 남아있던 항목, 아직 미착수. 웹(사진 갤러리·사진 요청)은 이미 구현됐으나 모바일 쪽 "사진 추가하기" 전용 화면은 screen-definitions.md에도 스텁으로만 존재 — 다음 사이클 후보 1순위(실기기 불필요, 바로 착수 가능).
6. **문서 정합성 점검 4차 필요 시점 예측** — L9(§6) 패턴대로면 PR #44(출판)·#47(모바일 UI 개편) 같은 큰 기능 PR 뒤엔 버전헤더·폴더트리 드리프트가 남기 쉽다. 이번엔 §3-4 작성과 동시에 `_INDEX.md`·CLAUDE.md·workflow-diagrams.md 버전 교차참조를 함께 재확인해 반영했다(신규 드리프트 없음 확인) — 다음 대형 PR 이후에도 이 습관을 유지 권고.

---

## 부록 — PR 목록

| PR | 제목 | 마이그레이션 |
|---|---|---|
| #1 | Do단계 보안 블로커 3건 + 동기화 계약 완성 (PII 암호화·실 인증·consent·멱등성) | 0002·0003·0004 |
| #2 | 인가 확대 — family-members·invitations·photo-requests + 초대 수락 계정 연결 | — |
| #3 | notifications 모듈 — 알림 수신 설정 + CTO B1 부수결함 수정 | 0005 |
| #4 | PII 2차 — contact 암호문+blind index, birth_date 암호화, name 평문 확정 | 0006 |
| #5 | social_worker 어르신 데이터 조회 fail-closed | — |
| #6 | 모바일 온보딩 화면 흐름 — 상태 호이스팅 | — |
| #7 | 무인증 요청 401(≠500) 수정 + 실 DB e2e 스크립트 2종 | — |
| #8 | 로컬 Keycloak realm + 실 인프라 인증 e2e (9/9) | — |
| #9 | PDCA Check — 설계문서↔구현 갭 분석 + 드리프트 동기화 | — |
| #10 | 모바일 앱 시작 게이트 — 온보딩 스킵·install_mode 분기·최초 동기화 화면 | — |
| #11 | import-linter — 모듈 경계·4계층 의존 규칙 CI 강제 | — |
| #12 | 본 Do 사이클 보고서 최초 작성 (PR #1~11 기준) | — |
| #13 | `core/auth.py` 순수화 — 리포지토리 조립을 `auth_deps.py`로 분리 (import-linter 예외 2건 제거) | — |
| #14 | 법무·인프라 결정 대기 트래커 | — |
| #15 | 챕터 Compaction Engine (§2.11 4단계 요약·키워드) — `sync/download`가 요약 내려보냄 | 0007 |
| #16 | Critic Agent (§2.11 3단계) — `questions` 큐에 생성 경로 신설, vLLM 서사 갭 분석 → 심층 질문 Top-3 | — |
| #17 | apps/web 알림 수신 설정 화면 (notifications 모듈 첫 웹 소비자) | — |
| #18 | apps/web Keycloak 로그인 연동 (Auth.js/NextAuth v5, decisions #49) — 웹 화면 전체가 실 Bearer로 동작 | — |
| #19 | apps/admin Keycloak 로그인 연동 (동일 Auth.js 방식) | — |
| #20 | PDCA Check #2 — PR #10~19 반영, 설계문서 스테일 5건(G7~G11) 정정 | — |
| #21 | apps/web·admin 공유 코드를 `packages/web-shared`로 추출 (npm 워크스페이스, decisions #50) | — |
| #22 | apps/web 가족 대시보드 "오늘의 기억 리포트"(WF1) — Compaction 요약 최초 노출, 정서 항목은 OFF 안내로 대체 | — |
| #23 | apps/mobile 홈 셸(M2) + 하단 탭 4개 — `AppShell`이 임시 `AssistantHomeScreen`을 대체 | — |
| #24 | 챕터 감수 승인 시 Compaction 재확인 안전망 (gap-analysis G11 후속 #3) | — |
| #25 | 본 Do 사이클 보고서 갱신 (PR #12~24 반영, §3-2 신설) | — |
| #26 | §4.2 Endpoint List를 실제 구현과 1:1로 정비 (gap-analysis G11, OpenAPI 스키마 전수 대조) | — |
| #27 | 단기 압축 기억(Persona) JSON 룰셋 서버측 생성 (§2.11 4단계, CareAgent 전용 스코프) | 0008 |
| #28 | 첫 가족 구성원 연결 — admin 중개 초대 경로 (decisions #51) | — |
| #29 | 결정 대기 트래커 완료 항목 갱신 (첫 가족 연결·페르소나 룰셋) | — |
| #30 | 온디바이스 SLM 벤치마크 프로토콜 + 측정 하니스 (실측은 미실행) | — |
| #31 | 법무·인프라·경영 미결 14건 일괄 확정 (decisions #52~#65, 순수 문서) | — |
| #32 | blind index 키를 `PII_KEK`에서 정식 분리 (decisions #60) | — |
| #33 | 가족 대리 동의 관리 화면 신규 (decisions #53) | — |
| #34 | 복지사 제3자제공 동의 게이트 구현 (decisions #54) | 0009 |
| #35 | 국외이전(FCM) 고지·동의 UI 추가 (decisions #57) | 0010 |
| #36 | self-hosted 관측 스택 구축 (decisions #61) | — |
| #37 | B2G 시설 테넌시 안전망 구축 (decisions #59) | 0011 |
| #39 | 보유기간·계정 삭제(erasure) 오케스트레이션 (decisions #56, Q5) — **법무·인프라·경영 14건 중 마지막 항목** | 0012 |
| #40 | 설계문서 최신화 — 코드 대비 드리프트 정정 + `data-classification-policy.md` 신규 | — |
| #41 | FP(기능점수) 기반 SW개발비 산정 내역서 신규 작성 (정통법) | — |
| #42 | FP 산정 내역서 간이법(Simplified Method) 버전 신규 작성 | — |
| #43 | 문서 정합성 전수점검 — 고아 `.bkit/` 삭제, structure.md 변경이력 재정렬, report.md CTO 블로커 상태표 정정 | — |
| #44 | Phase 3 출판 파이프라인 — `publications` 모듈 신규(reportlab/EbookLib 실 조판), apps/web `(family)/publications` | — |
| #45 | 말벗돌봄 대화 화면·세션·mock STT/SLM 최초 구현 | — |
| #46 | 화면설계서(UI/UX 전용) 신규 작성 — `docs/02-design/screen-definitions.md` | — |
| #47 | "은실이" 대화 전용 UI 전면 개편(decisions #66~#68) — 하단 4탭 제거, 신규 실 VAD, 페르소나 재명명 | — |
| #48 | 문서 정합성 전수점검 2차 — "은빛이" 잔존 표기 8곳·structure.md 모바일 트리 드리프트(6버전) 정정 | — |
| #49 | 웹 실 인증 세션 연결(decisions #69) — 신규 `GET /me`, apps/web `?userId=` 임시 패턴 제거 | — |
| #50 | 설계발표 PPT 신규 — 시스템 흐름·단위 시스템별 업무흐름도 시각화 중심 재구성(44슬라이드) | — |

> #38은 결번(머지되지 않음).
