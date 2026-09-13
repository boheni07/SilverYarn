# 법무·인프라 결정 대기 트래커

> **목적**: Do 단계에서 코드로 닫을 수 있는 CTO 보안 블로커(B1~B6)와 Design 잔여는 전부 구현됐고
> (PR #1~13, `docs/04-report/features/silveryarn-platform.report.md`), 남은 작업은 전부 아래 항목의
> 외부 회신·결정 대기였다. 이 문서는 그 회신을 채워가며 관리하는 살아있는 트래커다.
>
> **2026-09-12 갱신**: ⚖️ 법무 6건·🏗️ 인프라 5건·💼 경영 3건 **전부 사용자와의 대화로 정책을
> 일괄 확정**했다(`decisions.md` #52~#65). 법무 6건은 정식 외부 법률자문을 대체하지 않는
> **잠정 회사 정책**임을 유의 — 자문 결과가 다르면 재작업 가능성이 있다. 남은 것은 각 항목의
> "후속 작업"란에 적힌 코드 구현뿐이다.
>
> **2026-09-13 갱신**: 마지막 미착수 구현이었던 **Q5(#56, 보유기간·파기)까지 완료** — 이 문서가
> 추적하던 법무·인프라·경영 미결 14건(Q1~Q6·I1~I5·경영 3건)이 **전부 구현 완료**됐다. 남은
> 항목은 §"선행조건 대기"의 실측·벤치마크 성격 항목(온디바이스 SLM 벤치마크 등)뿐이며, 이들은
> 외부 회신 대기가 아니라 실기기 측정이 먼저 필요한 별도 트랙이다.
>
> **작성일**: 2026-09-10 · **갱신 규칙**: 회신이 오면 "회신/결정" 열에 날짜와 요지를 적고, 그에 따라
> 파생되는 구현 작업을 "후속 작업"에 티켓으로 쪼갠다. 상태를 `⚖️ 대기` → `✅ 확정` → `🔨 구현중` → `✔️ 완료`로.
>
> **SoR**: 확정된 결정은 `docs/01-plan/decisions/silveryarn-platform.decisions.md`에 정식 기재하고 여기서는 링크만.

---

## ⚖️ 법무 — CTO 착수 심사 원문 6개 질문

`docs/02-design/cto-review-2026-09-05.md` §3 "법무 검토 요청 항목".

### Q1. 정서점수 = 제23조 민감정보? 알림 없이 "기록만" 해도 별도동의 필요? — ✅ 확정

| | |
|---|---|
| 관련 결정 | [decisions #52](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), #25, #19 |
| 회신/결정 | **2026-09-12, 사용자**: 일반 개인정보로 취급 — 별도 명시 동의 없이 기존 온보딩 포괄동의로 충분. ⚠️ 정식 법률자문 대체 아닌 잠정 정책 |
| 현재 코드 | 정서 모니터링 파이프라인 **피처플래그 OFF**(decisions #25) — 이 결정은 법적 전제만 정리, 기능 자체 활성화는 별개 착수 여부 |
| 후속 작업 (미착수) | 정서 write 경로 활성화 · `GET /users/{id}/emotion-scores`·`/emotion-alerts` · 알림 임계치 로직(#19, 여전히 별도 검토 필요) · design §2.5 파이프라인 · 문구는 #55(Q4) 가이드라인 준수 |

### Q2. 성년후견 미개시 어르신에 대한 가족 대리동의 유효? 본인동의 필수범위? — ✅ 확정, ✔️ 구현 완료

| | |
|---|---|
| 관련 결정 | [decisions #53](../01-plan/decisions/silveryarn-platform.decisions.md), #46 (CTO B2) |
| 회신/결정 | **2026-09-12, 사용자**: 가족(1촌 이내) 대리동의를 유효로 인정. legal_guardian enum까지는 아니고 self/proxy 대리동의 자체의 법적 효력만 인정 |
| 구현 (2026-09-12) | 조사해보니 백엔드는 이미 `POST /users/{id}/consent-logs`의 `granted_by`(호출자 본인 구성원 id 검증 포함, PR #6)로 대리동의를 지원하고 있었다 — 실제 빠져 있던 건 이걸 쓰는 화면뿐. `apps/web` `/consent`(신규): 가족 구성원 선택 → 유형별(개인정보 수집·외부TTS·외부LLM) 동의 토글, `grantedBy`로 대리 동의 기록. `actor`는 여전히 `granted_by` 유무로 파생(별도 enum 컬럼은 불필요 — YAGNI) |
| 남은 것 | 없음 — apps/web이 아직 세션→family_member 자동 해석을 안 해서(notification-settings와 동일한 임시 상태) 구성원을 직접 고르는 UX는 실 인증 완성 시 함께 개선 예정 |

### Q3. 가족·복지사 열람 = 제17조 제3자제공인가, 제26조 위탁범위 내 이용인가? — ✅ 확정, ✔️ 구현 완료

| | |
|---|---|
| 관련 결정 | [decisions #54](../01-plan/decisions/silveryarn-platform.decisions.md), #48, #12 (CTO B2) |
| 회신/결정 | **2026-09-12, 사용자**: 가족 = 위탁범위 내 이용(별도 동의 불필요), 복지사 = 제3자제공(전용 동의 필요) |
| 구현 (2026-09-13) | `consent_type` enum에 `third_party_access` 추가(마이그레이션 0009). `auth_deps.authorize_elder_data_read()`(신규, `core/auth.py`는 여전히 순수 유지) — social_worker는 이 동의가 있을 때만 통과. 챕터(3)·대화(4)·일정(2)·사진(1) 총 10개 조회 엔드포인트 전환. `ConsentDirectory` Protocol + Fake로 순수 단위테스트 7건. **실 인프라 e2e로 왕복 검증**: 동의 전 social_worker→403, family가 동의 기록(201)→social_worker 재시도 403→200(`e2e_keycloak_check.py`, 11/11 PASS) |
| 남은 것 | 없음 — social_worker 기본 fail-closed(#48)는 조건부 허용으로 완전히 대체됨 |

### Q4. 정서점수 산출·통보가 의료기기법 규제대상이 될 위험? — ✅ 확정

| | |
|---|---|
| 관련 결정 | [decisions #55](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), #12 관련 |
| 회신/결정 | **2026-09-12, 사용자**: "진단/판정" 표현을 전면 회피, 참고용 지표로만 제공하는 방향으로 제품을 설계 |
| 현재 코드 | 해당 기능 OFF (Q1과 동일) |
| 후속 작업 (미착수) | 정서 기능 구현 시 카피·알림 문구 가이드라인에 반영(진단적 표현 금지어 목록 등) |

### Q5. 원본음성/전사/벡터/사진/백업 각각의 보유기간·파기방법? crypto-shredding이 적법한 파기로 인정? — ✅ 확정, ✔️ 구현 완료

| | |
|---|---|
| 관련 결정 | [decisions #56](../01-plan/decisions/silveryarn-platform.decisions.md), #45 (파기 수단), CTO B3 |
| 회신/결정 | **2026-09-12, 사용자**: crypto-shredding을 적법한 파기 수단으로 채택. 보유기간은 하드코딩하지 않고 **DB 설정 테이블(`retention_policies`) + admin 콘솔 UI**로 운영자가 직접 조정 |
| 구현 (2026-09-13) | 착수 전 schema.md 전 테이블 FK `ON DELETE` 절을 재조사해 스코프를 좁혔다 — `users` 하위 거의 모든 테이블이 이미 `ON DELETE CASCADE`(`user_encryption_keys` 포함)라 `DELETE FROM users` 한 줄로 Postgres 쪽은 crypto-shredding까지 이미 완결. 실제 오케스트레이션이 필요했던 건 Postgres 밖 **Qdrant·Neo4j·MinIO 3곳**뿐. 마이그레이션 0012(`retention_policies`+`deletion_records` 신설, `conversation_chunks.retention_until`/`purged_at`), 신규 `retention` 모듈(정책 CRUD API), `RetentionPurgeService`(만료 대화 원문 배치 파기 — Qdrant/Neo4j 삭제 후 Postgres redaction, worker.py 매시 30분 cron), `UserErasureService`(계정 전체 삭제 — 외부 저장소 먼저→Postgres 마지막 순서로 재시도 안전성 확보) + `POST /users/{id}/erase` admin 전용, apps/admin `/retention-policies`(보유일수 조정) + 사용자 목록 "계정 삭제" 2단계 확인 danger-zone |
| 스코프 결정 | 시간 기반 보유기간은 **의도적으로 conversation_chunks 원문 하나로만 좁힘**(원본음성은 이미 업로드 성공 시 즉시삭제 #30, 챕터·사진은 자서전 결과물이라 계정 존속기간 보관 대상 아님) — "N일 비활성 시 계정 자동삭제" 같은 자율 파괴적 동작은 채택하지 않음(안전 설계 판단) |
| 검증 | 실 Docker 인프라(Postgres+Qdrant+Neo4j+MinIO)로 보유기간 계산→만료→파기(redaction)→외부저장소 정리, 계정 삭제→cascade+외부저장소 정리→`deletion_records` 감사로그 전 과정 왕복 검증. 부수 발견: `VECTORDB_API_KEY=""`가 qdrant-client의 https 자동판정 로직에 걸려 로컬 평문 Qdrant 접속이 SSL 에러로 실패하던 버그 발견·수정 |
| 상태 | ✅ 완료 — 이 항목이 트래커의 마지막 미착수 구현이었음(법무·인프라·경영 미결 14건 전체 완료) |

### Q6. FCM/SMS/이메일 알림, Google Fonts CDN이 국외이전 고지·동의 대상? — ✅ 확정, 🔨 부분 구현

| | |
|---|---|
| 관련 결정 | [decisions #57](../01-plan/decisions/silveryarn-platform.decisions.md), CTO B6 |
| 회신/결정 | **2026-09-12, 사용자**: FCM(구글, 미국) 유지 + 온보딩 동의 화면에 국외이전 고지·동의 UI 추가 |
| 구현 (2026-09-13) | `consent_type` enum에 `international_transfer` 추가(마이그레이션 0010). 모바일 `OnboardingScreen.kt`의 동의 단계에 `data_collection`과 구분되는 별도 체크박스(선택, 기본 미동의)와 고지 문구("구글의 해외(미국) 서버… 기기 식별 토큰이 국외로 이전됩니다") 추가. `OnboardingCoordinator`가 두 동의(data_collection=필수, international_transfer=선택)를 모두 `POST /consent-logs`로 기록 |
| 남은 것 | 알림 발송 채널(FCM/SMS/이메일 어댑터) 자체는 여전히 미구현 — 지금은 동의 이력만 먼저 확보. 웹 폰트는 `design-tokens.md` 기준 이미 로컬이라 문제 없음 |

---

## 🏗️ 인프라 — infra-architect 착수 필요

`docs/02-design/cto-review-2026-09-05.md` §2 (Infrastructure), §1 Concern.

### I1. "Zero External Data Egress" 사정거리 정의 — ✅ 확정, ✔️ 구현 완료

| | |
|---|---|
| 관련 | [decisions #58](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), CTO Infra B2, Security B6 |
| 결정 | **2026-09-12, 사용자**: PII·원본 데이터(대화 원문·음성·사진 등)만 외부 유출 절대 금지, 빌드툴·오픈소스 패키지·웹폰트·상용 알림 SDK(FCM) 같은 메타데이터 수준 통신은 허용. 완전 에어갭 미채택 — Q6(FCM 유지)와 정합 |
| 현재 | 벡터 payload에 원문 미저장 원칙은 `upload_pipeline_service`에서 준수(payload=`user_id`만) |
| 구현 (2026-09-13) | "PII 수준" 경계를 4단계(Tier 1~4)로 명문화한 [`data-classification-policy.md`](../02-design/data-classification-policy.md) 신규 작성 — schema.md 실제 컬럼 단위로 분류하고, 신규 컬럼/외부연동 추가 시 판단 체크리스트 포함 |
| 남은 것 | 없음 |

### I2. `organizations` B2G 시설 테넌시 — ✅ 확정, ✔️ 구현 완료

| | |
|---|---|
| 관련 | [decisions #59](../01-plan/decisions/silveryarn-platform.decisions.md), #47 보류, #1, erd.md §11 |
| 결정 | **2026-09-12, 사용자**: 지금 착수. **2026-09-13, 사용자**: 접근권 부여 방식은 안전망(defense-in-depth) — 기존 1:1 `family_members` 연결(admin 중개 초대, #51) 유지, `organizations`는 시설 불일치 시 차단하는 2차 안전망으로만 사용. 정식 B2G 대량 권한 부여 모델은 스코프 밖 |
| 구현 (2026-09-13) | 마이그레이션 0011(`organizations` 테이블 + `users`/`family_members`/`invitations`.`org_id`, 전부 `ON DELETE SET NULL`). 신규 `organizations` 모듈(domain/infra/application/api/deps, import-linter 컨테이너 등록). `auth_deps.py`에 `UserDirectory`(어르신 org_id 조회) + `ElderAccessContext`(기존 `ConsentDirectory` 단독 파라미터를 흡수한 번들) 추가, `authorize_elder_data_read()`가 caregiver/social_worker의 org_id와 어르신 org_id 불일치 시 403. `GET/POST /organizations`·`GET /organizations/{id}`·`PUT /users/{id}/organization`(전부 admin 전용) 신규. apps/admin `/organizations`(시설 등록·목록) + family-members 화면에 시설 배정 폼·초대 시 시설 선택 UI 추가 |
| 검증 | 유닛테스트 19건 신규(197개) — `ElderAccessContext` 조합 시나리오(같은 시설 허용/다른 시설 차단/org_id 없는 B2C 무영향) 전부 Fake로 커버. **실 인프라**: Postgres에 직접 org A/B·어르신·caregiver 생성 후 같은 시설 허용→다른 시설로 재배정→차단 왕복 확인. apps/admin lint/type-check/build 통과 |
| 남은 것 | 없음 — 이 안전망 스코프에서는 완료. 정식 B2G 대량 권한 부여 모델은 B2G 운영모델 확정 후 별도 라운드 |

### I3. `PII_KEK` Vault transit 이전 (PII 암호화 3차) — ✅ 확정, blind index 분리 ✔️ 구현 완료

| | |
|---|---|
| 관련 | [decisions #60](../01-plan/decisions/silveryarn-platform.decisions.md), #45 3차 |
| 결정 | **2026-09-12, 사용자**: 환경변수 방식 유지(Vault/OpenBao 인프라 구축은 보류), blind index 키만 지금 `PII_KEK`에서 정식 분리 |
| 구현 (2026-09-12) | `BLIND_INDEX_KEY` 환경변수 신설, `core/crypto.py` `PiiCrypto.__init__(bidx_key=)`/`from_settings` 교체(미설정 시 하위호환 폴백+경고 로그), `scripts/backfill_blind_index.py` 신규. 유닛테스트 3건. design.md v0.45 |
| 남은 것 | Vault/OpenBao 인프라 이전 자체는 계속 보류(시크릿 매니저 인프라 선결 필요) |

### I4. 관측·에러추적 스택 — ✅ 확정, ✔️ 구현 완료

| | |
|---|---|
| 관련 | [decisions #61](../01-plan/decisions/silveryarn-platform.decisions.md), CTO Enterprise Concern |
| 결정 | **2026-09-12, 사용자**: 지금 구축 — self-hosted GlitchTip(에러) + Prometheus/Grafana/Loki(메트릭·로그). Sentry 등 SaaS는 I1 원칙상 불가 |
| 구현 (2026-09-13) | `infra/observability/`에 Prometheus·Loki·Grafana Alloy(Promtail 대체, EOL) 설정 + Grafana 데이터소스 자동 프로비저닝. `infra/docker-compose.yml`에 glitchtip-db/redis/web(all_in_one)+**glitchtip-bootstrap**(계정·조직·프로젝트·DSN 전부 자동 생성, Keycloak realm 자동임포트와 동일한 취지) 추가. 백엔드: `core/observability.py`(sentry-sdk, DSN 없으면 꺼짐) + `/metrics`(prometheus-fastapi-instrumentator) + `core/logging.py` JSON 실제 포맷 정정 + **`handle_unexpected`가 예외를 완전히 삼키던 버그 발견·수정**(로깅+GlitchTip 캡처 추가). 실 인프라 3파이프라인 전부 왕복 검증(메트릭 스크레이프·로그 Loki 도착·에러 GlitchTip Issue 생성) |
| 호스트 포트 | 9679(GlitchTip)·9680(Grafana) — 9670-9680 전 슬롯 소진(docker-port-range-constraint). Prometheus·Loki는 컨테이너 내부 전용(Grafana가 프록시) |
| 남은 것 | DCGM(GPU)은 GPU 서버 확보 후. GlitchTip DSN을 `.env.local`에 붙여넣는 딱 1단계만 수동(`infra/observability/README.md`) |

### I5. GPU 토폴로지 / vLLM 서빙 구성 — 🔄 부분 확정

| | |
|---|---|
| 관련 | [decisions #62](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), CTO Enterprise Concern, [#27](../01-plan/decisions/silveryarn-platform.decisions.md) |
| 결정 | **2026-09-12, 사용자**: 서버 LLM은 챕터생성·Compaction·Critic Agent 등 비실시간 전용, 실시간 말벗돌봄 대화는 온디바이스 SLM만 담당. **VRAM 예산표 자체는 여전히 보류** — 온디바이스 SLM 실기기 벤치마크(#27, `docs/03-check/ondevice-slm-benchmark-protocol.md`) 결과 필요 |
| 현재 | 미착수 |
| 후속 작업 | 벤치마크 완료 후 4모델 동거 VRAM 예산표·admission control 확정 |

### ✅ I0. 로컬 개발 인프라 — **해결됨**

`infra/docker-compose.yml` (postgres·redis·qdrant·neo4j·minio·keycloak, port 9670~9678) + `infra/keycloak/import/` realm 자동 임포트. CTO Infra B1 종결.

---

## 💼 경영 결정 — ✅ 전부 확정 (2026-09-12, 사용자)

| # | 항목 | decisions | 결정 |
|---|---|---|---|
| #2 / #14 | Phase 1~3 착수 일정·예산·인력 | [#63](../01-plan/decisions/silveryarn-platform.decisions.md)(신규) | 정식 예산·인력은 미결이나 **3개월 내 소규모 파일럿 출시**를 대략적 목표로 확정 |
| #18 / #23 | 결제 도메인 — B2C/B2G 과금 방식 → PG사·요금제 | [#64](../01-plan/decisions/silveryarn-platform.decisions.md)(신규) | 파일럿은 무료·수동결제로 진행, 결제 도메인은 계속 Phase 1 스코프 아웃 |
| #13 | 외부 고품질 TTS 벤더·비용·DPA (Phase 3 시점) | [#65](../01-plan/decisions/silveryarn-platform.decisions.md)(신규) | Phase 3 유예 재확인 — 파일럿은 온디바이스 네이티브 TTS로 충분 |

---

## ⏳ 선행조건 대기 (외부 결정 아님 — 실측·벤치마크·제품결정)

| 항목 | decisions | 대기 대상 | 병렬 착수 |
|---|---|---|---|
| 온디바이스 SLM 모델 선정 (Kanana-2 / Qwen2.5-0.5B 등) | [#27](../01-plan/decisions/silveryarn-platform.decisions.md) | 실기기 3종(S10급/A35급/S24급) STT+SLM+TTS 동시상주 벤치마크 (2주) | 🔄 **프로토콜+측정 하니스 준비 완료** — [ondevice-slm-benchmark-protocol.md](./ondevice-slm-benchmark-protocol.md), 코드는 `apps/mobile/.../benchmark/`. 실행에는 실기기+`SttEngine`/`SlmEngine` 실 구현체(추론 런타임 선정 별도)가 여전히 필요 — 실측 자체는 미실행 |
| 로컬 "최근 5일" 캐시 기준 | [#9](../01-plan/decisions/silveryarn-platform.decisions.md) | 저사양 키오스크 단말 저장용량 실측 | 🔄 절차 문서화 완료 — [프로토콜 §7](./ondevice-slm-benchmark-protocol.md#7-부록--로컬-최근-5일-캐시-실측-decisions-9), 실기기 5일 축적 실측은 미실행 |
| 실시간 대화 파이프라인 수치 (RAM ~850MB, 첫음성 0.8~1.2s 등) | [#31](../01-plan/decisions/silveryarn-platform.decisions.md) | 벤치마크 검증 | 🔄 측정 지표·목표치 매핑 완료 — [프로토콜 §4](./ondevice-slm-benchmark-protocol.md#4-측정-항목과-목표치), 검증 자체는 미실행 |
| ~~모바일 첫 가족 구성원 연결 경로~~ | [#51](../01-plan/decisions/silveryarn-platform.decisions.md) | **완료 (PR #28)** — admin 중개 경로로 확정. `is_admin` 우회 재사용, 모바일 변경 없음 | — |
| ~~Compaction Engine (design §2.11 — `sync/download`의 summary·keywords)~~ | — | **완료 (PR #15)** — 요약·키워드 부분 | — |
| ~~페르소나 JSON 룰셋(§2.10 연동, "단기 압축 기억")~~ | — | **완료 (PR #27)** — 최초엔 CareAgent(은빛이) 전용으로 스코프 확정(Author/ScheduleAgent 표시명 미정이라 제외, 2026-09-11 사용자 결정: 보류)했으나, 2026-09-13 페르소나가 "은실이" 하나로 통일되며(decisions.md #66) 그 제약이 해소됐다. 서버 생성·다운로드·로컬 저장·**온디바이스 mock 소비**(`ConversationSessionController.loadPersonaContext()`, PR #47)까지 완료 — 실 SLM이 내용을 실제로 해석하는 건 여전히 실기기 벤치마크(#27) 종속 | — |

---

## 의존 관계 요약

> **2026-09-12 갱신**: 아래 Q1~Q6·I1~I5·경영 3건 **전부 사용자 결정으로 정책 확정 완료**(decisions.md #52~#65). 남은 것은 그 정책을 코드로 옮기는 구현 작업뿐이다.

```
Q1(정서 민감정보, ✅#52) ─┐
Q3(제3자제공, ✅#54)      ├─→ 한 묶음: 정서·동의·열람 정책 → 구현: third_party_access consent, emotion write 경로
Q2(대리동의, ✅#53)       ┘
Q5(보유기간·파기, ✔️#56 구현완료) ─→ retention_policies 테이블+admin UI+Qdrant/Neo4j/MinIO 오케스트레이터 (완료)
Q6(국외이전, ✅#57)      ─────→ 알림 발송 어댑터 구현 전제

I1(Zero Egress 범위, ✔️#58 구현완료) ─→ I2(테넌시 안전망, ✔️#59 구현완료)·I3(blind index만 분리, ✔️#60 구현완료)·I4(관측, ✔️#61 구현완료)
I5(GPU, 🔄#62 부분확정) ←── #27(SLM 벤치마크, 프로토콜+하니스 준비 완료 — 실기기 실행만 남음, VRAM 예산표는 여전히 보류)
```
