# silveryarn-platform — Do 단계 사이클 보고서

> **작성일**: 2026-09-10 (§1 최초 작성 시점 — PR #1~11 기준. §1의 지표·서술은 그 시점 스냅샷으로 남겨두고, #12 이후 확장분은 아래 **§3-2**·부록에 이어 적었다)
> **갱신일**: 2026-09-11 — PR #12~24 반영
> **대상 사이클**: CTO 착수 심사(`docs/02-design/cto-review-2026-09-05.md`) 보안 블로커 해소 + Design v0.6→v0.39 잔여 구현
> **PR 범위**: #1 ~ #24 (전부 main squash 머지)
> **PDCA 위치**: Do 대부분 완료 → Check 2회(`docs/03-check/gap-analysis-2026-09-10.md`, `-11.md`) → 본 Report. 남은 항목은 전부 [`blocked-decisions-tracker.md`](../../03-check/blocked-decisions-tracker.md) 외부 회신 대기

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
| **B1** 정서 데이터는 "기록" 시점부터 위법 소지 | 정서 파이프라인 OFF, 알림 수신은 opt-in | 정서 파이프라인 피처플래그 OFF(decisions #25), `emotion_scores`/`emotion_alerts` 엔드포인트 미구현. `notification_settings.receives_emotion_alerts` 기본값 **opt-out(false)** + `(family_member_id, channel)` UNIQUE (PR #3, 마이그레이션 0005) | ✅ 코드분 완료 / ⚖️ 정서 모니터링 법적 기준은 법무 대기 (Phase 2) |
| **B2** 대리동의 법적 근거 공백 | 동의 주체(self/proxy/legal_guardian) 구분 | `consent` 모듈 신규(PR #1). `ConsentLog.actor`(self/proxy)를 `granted_by` 유무에서 파생. 온보딩이 `recordConsent(data_collection)` 호출 | 🟡 부분 — 명시적 enum(`legal_guardian`)·`data_subject` RBAC 행은 성년후견 대리동의 법적 근거 확정(decisions #12) 대기 |
| **B3** 보유기간·파기정책이 전 문서에 없음 | `retention_until`/`purged_at` + 파기 오케스트레이션 | **crypto-shredding 수단 확보**: 사용자 파기 = `user_encryption_keys` 행 삭제 → 그 사용자 PII 자유텍스트·contact·birth_date 전량 복호화 불가 (PR #1/#4). `e2e_pii_auth_check`가 실제로 검증 | 🟡 파기 수단만 / ⚖️ 보유기간 수치·5개 저장소(PG·MinIO·Qdrant·Neo4j·Room) 통합 삭제 오케스트레이션은 법무 회신 대기 — **미착수** |
| **B4** PII 암호화 방식 미결 = 스키마 결정, 이연 불가 | 애플리케이션 레벨 필드 암호화 + 사용자별 DEK | **완료**. `core/crypto.py` — Fernet(AES-128-CBC+HMAC), 사용자별 DEK를 `PII_KEK`로 랩핑(`user_encryption_keys`), `pii.v1.` 토큰 접두. 1차(PR #1): `chapters.body_text`·`chapter_revisions.body_text_snapshot`·`conversation_chunks.{transcript_on_device,transcript_server,assistant_response}`. 2차(PR #4): `family_members.contact`·`invitations.contact`(암호문 + `contact_bidx` HMAC 동등검색), `users.birth_date`(DATE→VARCHAR 암호문). `name`은 평문 확정 | ✅ 완료 / 🔜 3차: `PII_KEK` Vault transit 이전, blind index 키 정식 분리 |
| **B5** 인증/인가/테넌시/감사모델 구조적 공백 | Keycloak 실검증, RBAC/IDOR, 감사로그, 테넌시 | **대부분 완료**. Keycloak JWKS RS256 검증 + `sub`→`family_members.keycloak_sub` 매핑(PR #1). Device Token = `device_credentials` SHA-256(PR #1). `authorize_user_access(principal, user_id, roles, require_2fa)` RBAC + IDOR 방지 — 13개 라우터 적용(PR #1/#2). 초대 수락→계정 연결(PR #2). social_worker fail-closed(PR #5). `access_logs` HTTP 미들웨어 감사로그(PR #1). 무인증 401(≠500) 버그 수정(PR #7). 로컬 Keycloak realm + e2e(PR #8) | ✅ 인증·인가·감사 완료 / ⚖️ `organizations` B2G 시설 테넌시는 운영모델 확정 대기 — **미착수** |
| **B6** Zero External Data Egress가 설계 내부와 충돌 | egress 범위 정의 + 통제 | 벡터 payload에 원문 미저장 원칙은 `upload_pipeline_service`에서 준수(payload=`user_id`만). egress 범위 정의·네트워크 통제는 인프라 설계 과제 | ❌ **미착수** — 인프라 설계(infra-architect) 필요 |

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

> §1~4는 PR #1~11 시점 기준, §3-2는 #12~24까지 갱신했다. 상세·회신 관리는
> **[`docs/03-check/blocked-decisions-tracker.md`](../../03-check/blocked-decisions-tracker.md)** (살아있는 트래커) — 아래 "외부 결정 대기" 표는 그 문서의 요약이다.

### 외부 결정 대기 (착수 불가)

| 항목 | 블로커 | 대기 대상 |
|---|---|---|
| 보유기간 수치 + 5개 저장소 통합 파기 오케스트레이션 | B3 | ⚖️ 법무 — 보유기간·crypto-shredding 인정 여부 |
| 정서 모니터링 알림 법적/윤리 기준 | B1 | ⚖️ 법무·윤리 (Phase 2) |
| 대리동의 `legal_guardian` enum + `data_subject` RBAC | B2 | ⚖️ 법무 — 성년후견 대리동의 근거 (decisions #12) |
| social_worker 어르신 데이터 재포함 | B5 | ⚖️ 법무 — 제3자제공 여부 + 전용 consent 유형 (decisions #48) |
| `organizations` B2G 시설 테넌시 | B5 | 📋 B2G 운영모델 |
| Zero Egress 범위 정의 + 네트워크 통제 | B6 | 🏗️ infra-architect |
| `PII_KEK` Vault transit 이전 + blind index 키 분리 | B4 3차 | 🏗️ 시크릿 매니저 인프라 |

### 코드 후속 (착수 가능, 우선순위 낮음)

- ~~`core/auth.py` → 모듈 infrastructure 결합 제거~~ — **완료 (PR #13)**. `core/auth.py`는 순수(토큰 검증·인가 규칙·조회 포트 `FamilyMemberDirectory`/`DeviceTokenDirectory` Protocol), 리포지토리 조립은 `core_service/auth_deps.py`(composition root). import-linter contract ④의 예외가 3건 → 1건(`model_registry`만).
- ~~Compaction Engine (design §2.11)~~ — **요약·키워드 부분 완료 (PR #15, 감수 승인 시 재확인 안전망은 PR #24)**: `LLMClient.compact_chapter`(vLLM) + 업로드 파이프라인 best-effort 호출 + `chapters.compaction_*`(마이그레이션 0007). `sync/download`가 요약을 내려보냄(vLLM 미가동 시 `body_text` 앞 200자). **미구현**: "단기 압축 기억 JSON 룰셋"(페르소나, §2.10 연동) — 온디바이스 SLM/페르소나 배포 경로 확정 후.
- ~~apps/web·admin 공유 코드 추출~~ — **완료 (PR #21)**. npm 워크스페이스 + `packages/web-shared`(decisions #50).
- ~~웹 가족 대시보드 "오늘의 기억 리포트"~~ — **완료 (PR #22)**.
- ~~모바일 홈 셸(M2) + 하단 탭 4개~~ — **완료 (PR #23)**.
- ~~§4.2 endpoint 표 ↔ 구현 1:1 정비~~ — **완료 (PR #26, design.md v0.40)**. OpenAPI 스키마 전수 대조로 실제 갭이 G11이 지목한 6건보다 컸음을 확인(17행 추가 — `family-members` 목록/생성 전체 누락 등).
- **모바일 가족 초대 화면** — 첫 가족 구성원 연결 경로 설계 결정 후(웹 콘솔/admin 경로 vs device-token 부트스트랩 엔드포인트).
- **온디바이스 SLM 의도 라우터** (workflow-diagrams.md §19) — 모바일 홈 셸(PR #23)의 마이크 세션이 말벗돌봄 모드로 고정돼 있는 이유. 모델 선정(decisions #27, 실기기 벤치마크) 선행 필요.
- 온디바이스 STT/SLM/TTS 런타임 — 모델 선정(decisions #27, 실기기 벤치마크) 대기.

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

---

## 7. 다음 사이클 권고

1. **법무 회신 취합** — B1(정서)·B2(대리동의)·B3(보유기간)·B5(제3자제공)가 한 묶음. 회신이 오면 retention 정책 + 파기 오케스트레이션이 가장 큰 단일 작업. (2026-09-11 현재 전부 미회신)
2. **infra-architect 착수** — B6(egress), `organizations` 테넌시, `PII_KEK` Vault, GPU 토폴로지, 관측 스택(self-hosted). 온프레미스 배포 설계가 다음 병목.
3. **온디바이스 SLM 모델 선정 벤치마크**(decisions #27, 실기기) — 착수하면 §19 의도 라우터(현재 모바일 홈 셸에서 말벗돌봄 모드 고정, PR #23)와 §2.10 페르소나 JSON 룰셋(Compaction Engine 잔여, PR #15)이 같이 풀린다. 남은 코드 후속 중 **유일하게 외부 회신이 아니라 실기기 확보가 선결조건**인 항목.
4. (완료) ~~`core/auth.py` 포트 리팩터링~~ → PR #13. ~~apps/web·admin 공유 코드 추출~~ → PR #21. ~~§4.2 endpoint 표 정비~~ → PR #26.

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
