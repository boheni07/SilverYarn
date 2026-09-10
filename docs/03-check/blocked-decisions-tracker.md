# 법무·인프라 결정 대기 트래커

> **목적**: Do 단계에서 코드로 닫을 수 있는 CTO 보안 블로커(B1~B6)와 Design 잔여는 전부 구현됐고
> (PR #1~13, `docs/04-report/features/silveryarn-platform.report.md`), 남은 작업은 **전부 아래 항목의
> 외부 회신·결정 대기**다. 이 문서는 그 회신을 채워가며 관리하는 살아있는 트래커다.
>
> **작성일**: 2026-09-10 · **갱신 규칙**: 회신이 오면 "회신/결정" 열에 날짜와 요지를 적고, 그에 따라
> 파생되는 구현 작업을 "후속 작업"에 티켓으로 쪼갠다. 상태를 `⚖️ 대기` → `✅ 확정` → `🔨 구현중` → `✔️ 완료`로.
>
> **SoR**: 확정된 결정은 `docs/01-plan/decisions/silveryarn-platform.decisions.md`에 정식 기재하고 여기서는 링크만.

---

## ⚖️ 법무 — CTO 착수 심사 원문 6개 질문

`docs/02-design/cto-review-2026-09-05.md` §3 "법무 검토 요청 항목".

### Q1. 정서점수 = 제23조 민감정보? 알림 없이 "기록만" 해도 별도동의 필요?

| | |
|---|---|
| 관련 결정 | [decisions #12](../01-plan/decisions/silveryarn-platform.decisions.md), #25, #19 |
| 현재 코드 (임시) | 정서 모니터링 파이프라인 **피처플래그 OFF**(decisions #25). `emotion_scores`/`emotion_alerts` 테이블(마이그레이션 0001)만 존재, write 경로·엔드포인트 미구현. `notification_settings.receives_emotion_alerts` 기본 opt-out(false, 마이그레이션 0005) |
| 상태 | ⚖️ 대기 |
| 회신/결정 | _(미회신)_ |
| 후속 작업 | 정서 write 경로 활성화 · `GET /users/{id}/emotion-scores`·`/emotion-alerts` · 알림 임계치 로직(#19) · design §2.5 파이프라인 |

### Q2. 성년후견 미개시 어르신에 대한 가족 대리동의 유효? 본인동의 필수범위?

| | |
|---|---|
| 관련 결정 | [decisions #46](../01-plan/decisions/silveryarn-platform.decisions.md) (CTO B2) |
| 현재 코드 (임시) | `consent_logs.granted_by` 유무로 `actor`(self/proxy) **파생만**. CTO 권고인 명시적 enum(self/proxy/**legal_guardian**)·`data_subject` RBAC 행은 **미도입** — `legal_guardian`을 코드가 임의 정의할 수 없어서 |
| 상태 | ⚖️ 대기 |
| 회신/결정 | _(미회신)_ |
| 후속 작업 | `consent_logs.actor` enum 컬럼 마이그레이션 · 대리동의 RBAC · 온보딩 동의 화면의 대리동의 분기 |

### Q3. 가족·복지사 열람 = 제17조 제3자제공인가, 제26조 위탁범위 내 이용인가?

| | |
|---|---|
| 관련 결정 | [decisions #48](../01-plan/decisions/silveryarn-platform.decisions.md), #12 (CTO B2) |
| 현재 코드 (임시) | **social_worker fail-closed** — `core/auth.py` `READ_ELDER_DATA_ROLES`에서 제외. 챕터·사진·대화·일정 조회 차단, 정서 알림·본인 알림설정은 유지 |
| 상태 | ⚖️ 대기 |
| 회신/결정 | _(미회신)_ |
| 후속 작업 | 전용 consent 유형(`third_party_access` 등) 신설 · 그 동의 상태를 게이트로 social_worker 재포함 · design §7.1 RBAC 매트릭스 갱신 |

### Q4. 정서점수 산출·통보가 의료기기법 규제대상이 될 위험?

| | |
|---|---|
| 관련 결정 | #12 관련 |
| 현재 코드 (임시) | 해당 기능 OFF (Q1과 동일) |
| 상태 | ⚖️ 대기 |
| 회신/결정 | _(미회신)_ |
| 후속 작업 | 규제대상 판정 시 → 정서 기능 전면 재설계 또는 Phase 스코프 재조정 |

### Q5. 원본음성/전사/벡터/사진/백업 각각의 보유기간·파기방법? crypto-shredding이 적법한 파기로 인정?

| | |
|---|---|
| 관련 결정 | [decisions #45](../01-plan/decisions/silveryarn-platform.decisions.md) (파기 수단), CTO B3 |
| 현재 코드 (임시) | crypto-shredding **수단만 확보** — `user_encryption_keys` 행 삭제 → 해당 사용자 PII 자유텍스트·contact·birth_date 전량 복호화 불가(`e2e_pii_auth_check.py`가 실제 검증). `*.retention_until`/`*.purged_at` 컬럼 **없음**, 5개 저장소(PostgreSQL·MinIO·Qdrant·Neo4j·온디바이스 Room) 통합 삭제 오케스트레이션 **미착수** |
| 상태 | ⚖️ 대기 — **가장 큰 단일 작업. 온보딩·동의 모듈 안정화의 선결조건** (CTO 추정 2~3주) |
| 회신/결정 | _(미회신)_ |
| 후속 작업 | 저장소·데이터 종류별 보유기간 표 · `retention_until`/`purged_at` 스키마 마이그레이션 · 파기 배치(arq cron) · 5-store 삭제 오케스트레이터 · crypto-shredding 적법성 확정 시 파기 트리거로 채택 · design §7.2 백업 정책 갱신 |

### Q6. FCM/SMS/이메일 알림, Google Fonts CDN이 국외이전 고지·동의 대상?

| | |
|---|---|
| 관련 결정 | CTO B6, Enterprise Concern |
| 현재 코드 (임시) | 알림 발송 채널 미구현(`notification_settings`는 "누가·어디로" 선택만). 웹 폰트는 `design-tokens.md` 기준 로컬 |
| 상태 | ⚖️ 대기 |
| 회신/결정 | _(미회신)_ |
| 후속 작업 | 알림 발송 어댑터 구현(FCM/SMS/이메일) · 국외이전 고지·동의 UI · 폰트 self-host 강제 |

---

## 🏗️ 인프라 — infra-architect 착수 필요

`docs/02-design/cto-review-2026-09-05.md` §2 (Infrastructure), §1 Concern.

### I1. "Zero External Data Egress" 사정거리 정의

| | |
|---|---|
| 관련 | CTO Infra B2, Security B6 |
| 현재 | 벡터 payload에 원문 미저장 원칙은 `upload_pipeline_service`에서 준수(payload=`user_id`만). 네트워크 통제·egress 프록시 **없음** |
| 상태 | 🏗️ 대기 — **나머지 인프라 항목의 상위 제약** (완전 에어갭이면 공수 2배) |
| 결정 | _(미결)_ |
| 후속 작업 | egress 3등급 분류(절대금지/허용+통제/즉시제거) · default-deny + allowlist 프록시 · 빌드타임 검증된 미러 정책 · 법무(위탁계약·국외이전) 병행 |

### I2. `organizations` B2G 시설 테넌시

| | |
|---|---|
| 관련 | [decisions #47](../01-plan/decisions/silveryarn-platform.decisions.md) 보류, #1, erd.md §11 |
| 현재 | `organizations` 테이블·`family_members.org_id` 없음. B2G 시설 간 열람 격리 불가 |
| 상태 | 📋 대기 — B2G 운영모델 확정 필요 |
| 결정 | _(미결)_ |
| 후속 작업 | `organizations` 테이블 + `family_members.org_id` 마이그레이션 · 테넌시 인가 술어(시설 경계) · admin 콘솔 시설 관리 |

### I3. `PII_KEK` Vault transit 이전 (PII 암호화 3차)

| | |
|---|---|
| 관련 | [decisions #45](../01-plan/decisions/silveryarn-platform.decisions.md) 3차 |
| 현재 | KEK를 환경변수 `PII_KEK`로 주입(MultiFernet 회전 대비). `core/crypto.py`의 `PiiCrypto` 생성 지점만 교체하면 됨. blind index 키는 KEK 첫 키에서 유도(정식 분리 안 됨) |
| 상태 | 🏗️ 대기 — 시크릿 매니저 인프라 확정 |
| 결정 | _(미결)_ |
| 후속 작업 | Vault/OpenBao + External Secrets Operator · `PiiCrypto` KEK 소스 교체 · blind index 키 정식 분리 + 백필 · MinIO SSE-KMS(원본음성) |

### I4. 관측·에러추적 스택

| | |
|---|---|
| 관련 | CTO Enterprise Concern |
| 현재 | 없음. Sentry SaaS는 Zero Egress상 사용 불가 |
| 상태 | 🏗️ 대기 |
| 결정 | _(미결)_ |
| 후속 작업 | self-hosted GlitchTip(에러) · Prometheus+Grafana+Loki(메트릭·로그) · DCGM(GPU) |

### I5. GPU 토폴로지 / vLLM 서빙 구성

| | |
|---|---|
| 관련 | CTO Enterprise Concern, [decisions #27](../01-plan/decisions/silveryarn-platform.decisions.md) |
| 현재 | 미착수. 서버 LLM의 실시간 대화 관여 여부도 미정(design §2.12) |
| 상태 | 🏗️ 대기 — 온디바이스 SLM 벤치마크(#27) 후 |
| 결정 | _(미결)_ |
| 후속 작업 | 4모델 동거 VRAM 예산표 · admission control · 서버 LLM 역할 확정(챕터생성 전용 vs 실시간) |

### ✅ I0. 로컬 개발 인프라 — **해결됨**

`infra/docker-compose.yml` (postgres·redis·qdrant·neo4j·minio·keycloak, port 9670~9678) + `infra/keycloak/import/` realm 자동 임포트. CTO Infra B1 종결.

---

## 💼 경영 결정 (참고 — 법무·인프라 아님)

| # | 항목 | decisions |
|---|---|---|
| #2 / #14 | Phase 1~3 착수 일정·예산·인력 | [#14](../01-plan/decisions/silveryarn-platform.decisions.md) |
| #18 / #23 | 결제 도메인 — B2C/B2G 과금 방식 → PG사·요금제 | [#23](../01-plan/decisions/silveryarn-platform.decisions.md) |
| #13 | 외부 고품질 TTS 벤더·비용·DPA (Phase 3 시점) | [#13](../01-plan/decisions/silveryarn-platform.decisions.md) |

---

## ⏳ 선행조건 대기 (외부 결정 아님 — 실측·벤치마크·제품결정)

| 항목 | decisions | 대기 대상 | 병렬 착수 |
|---|---|---|---|
| 온디바이스 SLM 모델 선정 (Kanana-2 / Qwen2.5-0.5B 등) | [#27](../01-plan/decisions/silveryarn-platform.decisions.md) | 실기기 3종(S10급/A35급/S24급) STT+SLM+TTS 동시상주 벤치마크 (2주) | ✅ 예산과 무관하게 지금 가능 |
| 로컬 "최근 5일" 캐시 기준 | [#9](../01-plan/decisions/silveryarn-platform.decisions.md) | 저사양 키오스크 단말 저장용량 실측 | 벤치마크와 함께 |
| 실시간 대화 파이프라인 수치 (RAM ~850MB, 첫음성 0.8~1.2s 등) | [#31](../01-plan/decisions/silveryarn-platform.decisions.md) | 벤치마크 검증 | 벤치마크와 함께 |
| 모바일 첫 가족 구성원 연결 경로 | — | 제품 결정: 웹 콘솔/admin 경로 vs device-token 부트스트랩 엔드포인트 (design §2.9, mobile-schema v0.8) | 결정 즉시 화면 1건 |
| ~~Compaction Engine (design §2.11 — `sync/download`의 summary·keywords)~~ | — | **완료 (PR #15)** — 요약·키워드 부분. 페르소나 JSON 룰셋(§2.10)만 남음 | — |

---

## 의존 관계 요약

```
Q1(정서 민감정보) ─┐
Q3(제3자제공)      ├─→ 한 묶음: 정서·동의·열람 정책
Q2(대리동의)       ┘
Q5(보유기간·파기) ─────→ retention 정책 = 온보딩·동의 모듈 안정화의 선결조건 (최대 단일작업)
Q6(국외이전)      ─────→ 알림 발송 실구현 전제

I1(Zero Egress 범위) ─→ I2(테넌시)·I3(Vault)·I4(관측)의 상위 제약
I5(GPU) ←── #27(SLM 벤치마크, 지금 병렬 착수 가능)
```
