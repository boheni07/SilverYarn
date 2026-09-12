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

### Q3. 가족·복지사 열람 = 제17조 제3자제공인가, 제26조 위탁범위 내 이용인가? — ✅ 확정

| | |
|---|---|
| 관련 결정 | [decisions #54](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), #48, #12 (CTO B2) |
| 회신/결정 | **2026-09-12, 사용자**: 가족 = 위탁범위 내 이용(별도 동의 불필요), 복지사 = 제3자제공(전용 동의 필요) |
| 현재 코드 | **social_worker fail-closed** — `core/auth.py` `READ_ELDER_DATA_ROLES`에서 제외 |
| 후속 작업 (미착수) | `third_party_access` consent 유형 신설 · 그 동의 상태를 게이트로 social_worker `READ_ELDER_DATA_ROLES` 재포함 · design §7.1 RBAC 매트릭스 갱신 |

### Q4. 정서점수 산출·통보가 의료기기법 규제대상이 될 위험? — ✅ 확정

| | |
|---|---|
| 관련 결정 | [decisions #55](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), #12 관련 |
| 회신/결정 | **2026-09-12, 사용자**: "진단/판정" 표현을 전면 회피, 참고용 지표로만 제공하는 방향으로 제품을 설계 |
| 현재 코드 | 해당 기능 OFF (Q1과 동일) |
| 후속 작업 (미착수) | 정서 기능 구현 시 카피·알림 문구 가이드라인에 반영(진단적 표현 금지어 목록 등) |

### Q5. 원본음성/전사/벡터/사진/백업 각각의 보유기간·파기방법? crypto-shredding이 적법한 파기로 인정? — ✅ 확정

| | |
|---|---|
| 관련 결정 | [decisions #56](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), #45 (파기 수단), CTO B3 |
| 회신/결정 | **2026-09-12, 사용자**: crypto-shredding을 적법한 파기 수단으로 채택. 보유기간은 하드코딩하지 않고 **DB 설정 테이블(`retention_policies`) + admin 콘솔 UI**로 운영자가 직접 조정 |
| 현재 코드 | crypto-shredding **수단만 확보**(`user_encryption_keys` 삭제). `*.retention_until`/`*.purged_at` 컬럼·5-store 통합 삭제 오케스트레이션 **미착수** |
| 상태 | 🔨 구현 대기 — **가장 큰 단일 작업** (CTO 추정 2~3주) |
| 후속 작업 (미착수) | `retention_policies` 테이블(데이터종류별 보유일수) 마이그레이션 · `retention_until`/`purged_at` 컬럼 · apps/admin 보유기간 설정 화면 · 5-store(PostgreSQL·MinIO·Qdrant·Neo4j·모바일 Room) crypto-shredding 오케스트레이터(arq cron) · design §7.2 백업 정책 갱신 |

### Q6. FCM/SMS/이메일 알림, Google Fonts CDN이 국외이전 고지·동의 대상? — ✅ 확정

| | |
|---|---|
| 관련 결정 | [decisions #57](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), CTO B6 |
| 회신/결정 | **2026-09-12, 사용자**: FCM(구글, 미국) 유지 + 온보딩 동의 화면에 국외이전 고지·동의 UI 추가 |
| 현재 코드 | 알림 발송 채널 미구현. 웹 폰트는 `design-tokens.md` 기준 로컬(문제 없음) |
| 후속 작업 (미착수) | 알림 발송 어댑터 구현(FCM/SMS/이메일) · 온보딩 동의 화면에 국외이전 고지·동의 항목 추가 |

---

## 🏗️ 인프라 — infra-architect 착수 필요

`docs/02-design/cto-review-2026-09-05.md` §2 (Infrastructure), §1 Concern.

### I1. "Zero External Data Egress" 사정거리 정의 — ✅ 확정

| | |
|---|---|
| 관련 | [decisions #58](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), CTO Infra B2, Security B6 |
| 결정 | **2026-09-12, 사용자**: PII·원본 데이터(대화 원문·음성·사진 등)만 외부 유출 절대 금지, 빌드툴·오픈소스 패키지·웹폰트·상용 알림 SDK(FCM) 같은 메타데이터 수준 통신은 허용. 완전 에어갭 미채택 — Q6(FCM 유지)와 정합 |
| 현재 | 벡터 payload에 원문 미저장 원칙은 `upload_pipeline_service`에서 준수(payload=`user_id`만) |
| 후속 작업 (미착수) | "PII 수준" 경계를 CONVENTIONS.md 또는 별도 보안정책 문서에 명문화 |

### I2. `organizations` B2G 시설 테넌시 — ✅ 확정 (지금 착수)

| | |
|---|---|
| 관련 | [decisions #59](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), #47 보류, #1, erd.md §11 |
| 결정 | **2026-09-12, 사용자**: 지금 착수 — organizations 테이블 + 시설 경계 인가 |
| 현재 | `organizations` 테이블·`family_members.org_id` 없음. B2G 시설 간 열람 격리 불가 |
| 후속 작업 (미착수) | `organizations` 테이블 + `family_members.org_id` 마이그레이션 · 테넌시 인가 술어(시설 경계) · admin 콘솔 시설 관리 |

### I3. `PII_KEK` Vault transit 이전 (PII 암호화 3차) — ✅ 확정, blind index 분리 ✔️ 구현 완료

| | |
|---|---|
| 관련 | [decisions #60](../01-plan/decisions/silveryarn-platform.decisions.md), #45 3차 |
| 결정 | **2026-09-12, 사용자**: 환경변수 방식 유지(Vault/OpenBao 인프라 구축은 보류), blind index 키만 지금 `PII_KEK`에서 정식 분리 |
| 구현 (2026-09-12) | `BLIND_INDEX_KEY` 환경변수 신설, `core/crypto.py` `PiiCrypto.__init__(bidx_key=)`/`from_settings` 교체(미설정 시 하위호환 폴백+경고 로그), `scripts/backfill_blind_index.py` 신규. 유닛테스트 3건. design.md v0.45 |
| 남은 것 | Vault/OpenBao 인프라 이전 자체는 계속 보류(시크릿 매니저 인프라 선결 필요) |

### I4. 관측·에러추적 스택 — ✅ 확정 (지금 구축)

| | |
|---|---|
| 관련 | [decisions #61](../01-plan/decisions/silveryarn-platform.decisions.md)(신규), CTO Enterprise Concern |
| 결정 | **2026-09-12, 사용자**: 지금 구축 — self-hosted GlitchTip(에러) + Prometheus/Grafana/Loki(메트릭·로그). Sentry 등 SaaS는 I1 원칙상 불가 |
| 현재 | 없음 |
| 후속 작업 (미착수) | `infra/docker-compose.yml`에 GlitchTip·Prometheus·Grafana·Loki 추가(port 9670~9680 범위) · 백엔드 에러 리포팅 SDK 연동 · structlog→Loki 파이프라인 · DCGM(GPU)는 GPU 서버 확보 후 |

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
| ~~페르소나 JSON 룰셋(§2.10 연동, "단기 압축 기억")~~ | — | **완료 (PR #27)** — CareAgent(은빛이) 전용으로 스코프 확정(Author/ScheduleAgent 표시명 미정이라 제외, 2026-09-11 사용자 결정: 보류). 서버 생성·다운로드·로컬 저장까지 완료, **온디바이스 SLM 소비만 남음**(아래 벤치마크 항목에 종속) | — |

---

## 의존 관계 요약

> **2026-09-12 갱신**: 아래 Q1~Q6·I1~I5·경영 3건 **전부 사용자 결정으로 정책 확정 완료**(decisions.md #52~#65). 남은 것은 그 정책을 코드로 옮기는 구현 작업뿐이다.

```
Q1(정서 민감정보, ✅#52) ─┐
Q3(제3자제공, ✅#54)      ├─→ 한 묶음: 정서·동의·열람 정책 → 구현: third_party_access consent, emotion write 경로
Q2(대리동의, ✅#53)       ┘
Q5(보유기간·파기, ✅#56) ─────→ retention_policies 테이블+admin UI+5-store 오케스트레이터 (최대 단일작업, 미착수)
Q6(국외이전, ✅#57)      ─────→ 알림 발송 어댑터 구현 전제

I1(Zero Egress 범위, ✅#58) ─→ I2(테넌시, ✅#59 지금착수)·I3(blind index만 분리, ✅#60)·I4(관측, ✅#61 지금구축)
I5(GPU, 🔄#62 부분확정) ←── #27(SLM 벤치마크, 프로토콜+하니스 준비 완료 — 실기기 실행만 남음, VRAM 예산표는 여전히 보류)
```
