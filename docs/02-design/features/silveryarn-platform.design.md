---
template: design
version: 1.3
---

# silveryarn-platform Design Document

> **Summary**: 온디바이스 오프라인 우선 + 온프레미스 서버 하이브리드 아키텍처 기술 설계
>
> **Project**: 은빛실타래 (SilverYarn)
> **Version**: 0.39 (`POST /chapters/{id}/review` 승인 시 Compaction 재확인 안전망 — gap-analysis-2026-09-11 G11 후속 #3)
> **Author**: NUBiz AX(AI Transformation) Initiative
> **Date**: 2026-09-08
> **Status**: Draft
> **Planning Doc**: [silveryarn-platform.plan.md](../../01-plan/features/silveryarn-platform.plan.md)

### Pipeline References

| Phase | Document | Status |
|-------|----------|--------|
| Phase 1 | [Schema Definition](../../01-plan/schema.md) | ✅ 완료 (17개 엔티티, v1.4) — 시각 ERD: [erd.md](../../01-plan/erd.md) |
| Phase 2 | [Coding Conventions](../../../CONVENTIONS.md) | ✅ 완료 |
| Phase 3 | Mockup — [BI 가이드](../../../Plan/은빛실타래_BI가이드_v2.html), [UI/UX 화면설계서](../../../Plan/은빛실타래_UIUX_화면설계서.html), [design-tokens.md](../design-tokens.md) | ✅ (원본 산출물 + 토큰 문서화 + 접근성 최소기준 완료) |
| Phase 4 | API Spec — [sync-contract.md](../sync-contract.md) | ✅ 완료 (§4 + 동기화 계약 확정, 상세 OpenAPI 스펙은 Do 단계) |

> 본 문서는 `Plan/어르신_자서전_말벗돌봄_기획서.md`(3~9장) 및 `Plan/자서전_말벗돌봄_프로세스_흐름도.md`의 내용을 bkit PDCA Design 형식으로 정리한 것이며, 세부 다이어그램·검토자료는 원본 문서를 참조한다. **v0.2는 `design-validator` 검증 리포트(2026-09-05)의 발견사항을 반영한 개정판이다.**

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | 어르신 삶의 기록 소실 방지 + 독거·고립 돌봄 공백 해소, 저사양/재활용 단말·비상시 인터넷 환경 대응 |
| **WHO** | 어르신 본인(1차), 가족·요양보호사·복지사(2차), 복지관·지자체(잠재) |
| **RISK** | 초민감 개인정보(가족사·건강) 처리 리스크 — 온프레미스 원칙 위반 시 파급력 큼 |
| **SUCCESS** | Phase 1 MVP: 오프라인 대화 + Wi-Fi 배치 동기화 기본 흐름 검증 |
| **SCOPE** | Phase 1(작가+오프라인 코어) → Phase 2(말벗돌봄) → Phase 3(비서+외부연계) |

---

## 1. Overview

### 1.1 Design Goals

- 인터넷 연결 없이도 3대 모드(작가/말벗돌봄/비서)가 온디바이스 자원만으로 완결 동작
- 등록 Wi-Fi 접속 시에만 자동·백그라운드로 배치 동기화(업/다운로드) 수행
- 원본 구술 음성·자서전 원고 등 PII 포함 데이터는 100% 온프레미스 처리 (Zero External Data Egress)
- 사진 업로드(가족/당사자 무관)가 별도 조작 없이 자연스러운 회고 대화로 이어지고, 결과가 자서전 챕터에 자동 인라인 편입
- 단말 사양에 따라 설치 시점에 키오스크/일반 앱 모드로 자동 분기하되 기능은 완전히 동일하게 유지

### 1.2 Design Principles

- **오프라인 우선(Offline-First)**: 로컬 캐시 범위 내에서 항상 응답 가능해야 하며, 서버는 정확도 보정·정교화 역할
- **전면 온프레미스(On-Premise Only for PII)**: 외부 연계는 비식별화 + Opt-in인 경우에만, 그 외 전량 자체 인프라
- **모드 무관 결과 일치**: 작가 모드/말벗돌봄 모드 어디서 트리거되든 사진 회고·구술 결과는 동일 파이프라인으로 챕터에 편입
- **설치모드-기능 분리**: 키오스크/일반 앱은 설치·잠금 방식만 다르고 3대 운영 모드 기능은 완전히 동일

---

## 2. Architecture Options

### 2.0 Architecture Comparison

원본 기획서(3장)에서 이미 하이브리드 아키텍처가 확정되어 있으므로, 여기서는 그 확정안(Option B)과 대안을 비교해 선택 근거를 명시한다.

| Criteria | Option A: 완전 클라우드(서버 상시 연결) | Option B: 온디바이스-온프레미스 하이브리드 (선정) | Option C: 완전 온디바이스(서버 없음) |
|----------|:-:|:-:|:-:|
| **오프라인 대응** | 불가 | 가능 (평소 대화 전량 오프라인) | 가능하나 정교화 불가 |
| **데이터 주권** | 취약(상시 전송) | 강함(PII 전량 온프레미스) | 강함(단, 협업/감수 불가) |
| **정확도/개인화** | 높음(상시 최신) | 높음(Wi-Fi 동기화 시 정교화) | 낮음(저사양 SLM 한계) |
| **가족 협업(웹 콘솔)** | 가능 | 가능 | 불가 |
| **복잡도** | 낮음 | 높음 | 중간 |
| **Recommendation** | 시니어 오프라인 환경 부적합 | **선정 — 오프라인 요구+데이터주권+협업 모두 충족** | 협업·정교화 기능 상실 |

**Selected**: Option B — **Rationale**: 시니어 생활환경상 상시 인터넷 연결을 기대하기 어렵고, 초민감 개인정보를 다루므로 온프레미스 원칙이 필수이며, 가족 감수·협업을 위해 서버측 웹 콘솔이 필요.

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 📱 모바일앱 — 온디바이스 (오프라인 우선)                          │
│  Mic→VAD→On-Device STT→On-Device SLM/Router→TTS                 │
│  로컬 저장소: 최근 5일(잠정) 대화·자서전 캐시·경량 RAG·사진·미회고큐 │
└───────────────┬───────────────────────────────────────┬─────────┘
                │ Wi-Fi 접속 시 업로드                    │ 다운로드
                ▼                                         │
┌─────────────────────────────────────────────────────────────────┐
│ 🖥️ 서버 — 전량 온프레미스 (Python/FastAPI)                       │
│  API Gateway(Keycloak SSO)/오케스트레이터                        │
│    → [작가엔진|말벗돌봄엔진|비서엔진]                             │
│  → RAG·LLM Core(vLLM/A100, BGE-M3) → VectorDB(Qdrant)/         │
│    지식그래프(Neo4j)/RDB(Pg)/Object Storage(MinIO)               │
└───────────────┬───────────────────────────────────────┬─────────┘
                │                                         │
                ▼                                         ▼
        ┌──────────────┐                          ┌───────────────┐
        │ 🖊️ 웹 콘솔    │                          │ 🔌 선택·Opt-in │
        │ (Next.js —    │                          │ 외부 고품질TTS │
        │  자서전/가족/  │                          │ (비식별화 한정,│
        │  관리자)      │                          │  Phase 3)      │
        └──────────────┘                          └───────────────┘
```

> 상세 Mermaid 다이어그램(전체 통합 흐름도, 서버 모듈별 흐름, 상태머신 등 20+개)은 [`Plan/자서전_말벗돌봄_프로세스_흐름도.md`](../../../Plan/자서전_말벗돌봄_프로세스_흐름도.md) 참조. "최근 5일" 캐시 윈도우는 아직 잠정값이다([decisions.md #9](../../01-plan/decisions/silveryarn-platform.decisions.md) — 벤치마크 후 재확정).

### 2.2 Data Flow (오프라인 구술 → 동기화 → 챕터 반영)

```
[오프라인] 구술 발화 → On-Device STT/SLM 즉시 응답
  → 원본음성+1차전사 로컬 저장(최근 5일 윈도우, 잠정)
[Wi-Fi 접속 감지] 자동 업로드(음성+전사+신규사진)
  → 서버: 고정밀 STT 재전사 → 기존 청크와 Diff 비교(§2.8) → 신규분만 처리
  → 청킹/메타태깅 → 임베딩 → Vector DB Upsert
  → LLM 챕터 초안 생성/갱신 → 가족 웹 감수 대기열 등록
  → (승인) 챕터 확정 및 chapter_revisions 기록 / (반려) [workflow-diagrams.md §7](../workflow-diagrams.md) 재생성 루프
  → 자동 다운로드(최신 자서전·RAG스냅샷·사진·질문목록)
  → 로컬 캐시 갱신
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| 온디바이스 SLM/Router | On-Device STT, 로컬 SQLite FTS5(Phase 1 기본, [decisions.md #32](../../01-plan/decisions/silveryarn-platform.decisions.md)) | 오프라인 의도분류·응답생성 |
| 자서전 작가 엔진(서버) | RAG Core(Qdrant), 지식그래프(Neo4j), LLM(vLLM) | 챕터 초안 생성·갱신, 사진 인라인 삽입, 인물·사건·감정 관계 추적([decisions.md #29](../../01-plan/decisions/silveryarn-platform.decisions.md)) |
| 말벗돌봄 엔진(서버) | RAG Core, 정서 모니터링 모듈(§2.5) | 초개인화 회상 대화, 정서 점수 산출 |
| 비서·일정 엔진(서버/온디바이스) | RDB(PostgreSQL)/로컬 SQLite | 일정·복약 엔티티 저장, 알림 예약 |
| 동기화 게이트웨이 | 인증(**Keycloak SSO 확정** — [decisions.md #17](../../01-plan/decisions/silveryarn-platform.decisions.md)), Object Storage(MinIO) | 업/다운로드 처리, 체크섬 검증, 재시도 |
| 웹 콘솔(Next.js) | 동기화 게이트웨이, RDB, Object Storage | 원고 감수, 사진/타임라인, 인쇄용 조판(§2.6) |
| 출판 파이프라인(§2.6) | Object Storage(MinIO), 조판 엔진 | PDF/ePub 생성 |

### 2.4 RAG 검색(Retrieval) 파이프라인 — 신규 v0.2

> 원본 프로세스흐름도 2.2절의 인덱싱/검색 파이프라인을 Design 문서에 명시 (design-validator E-4).

```
사용자 발화 → Query 임베딩(BGE-M3)
  → 하이브리드 서치(BM25 + Dense, Qdrant)
  → 메타 필터(시기·인물 — conversation_chunks.meta_period/meta_people)
  → Top-K 청크 추출 → Re-rank → LLM Context 구성 → 응답 생성
```

인덱싱 파이프라인(신규 청크 → 임베딩 → 메타태깅 → Vector DB Upsert → 경량화 스냅샷 → 모바일 배포 큐)은 §2.2 Data Flow와 동일 경로를 공유한다.

### 2.5 정서 모니터링 처리 흐름 — 신규 v0.2

> design-validator E-2(처리 흐름 누락)·B-2(일별 점수 저장처 없음) 반영. `emotion_scores`(일별 시계열)와 `emotion_alerts`(임계치 초과 시 생성)를 분리해 사용한다([schema.md §3.12](../../01-plan/schema.md)).

```
말벗돌봄 대화 음성/텍스트 → 발화 톤 분석 + 부정 어휘 빈도 분석
  → 정서 점수 산출 → emotion_scores에 일별 1건 기록(항상 수행)
  → 임계치 초과? ─No→ 종료
                  ─Yes→ emotion_alerts 생성 → notification_settings 조회
                        → 설정된 채널로 가족·복지사 알림 발송
                        → 확인 응답? ─No(N분 경과)→ 재알림(에스컬레이션)
                                     ─Yes→ 케이스 종료(closed_at 기록)
```

> **알림을 발송할지 말지의 임계치 자체**는 법무·윤리 검토 대기 중이다([decisions.md #12](../../01-plan/decisions/silveryarn-platform.decisions.md)). 위 흐름의 "임계치 초과?" 분기 로직은 검토 완료 후 구현하며, "설정된 채널로 발송"(수신자·채널 선택)만 지금 구현 가능하다([decisions.md #19](../../01-plan/decisions/silveryarn-platform.decisions.md)).

### 2.6 출판/인쇄 파이프라인 — 신규 v0.2

> 기획서 3.3(MinIO "완성 PDF/ePub")·6장(자동 조판)·흐름도 2.4(Publish→Print) 및 In Scope 선언 항목을 반영 (design-validator E-1). 엔티티: `publications`([schema.md §3.17](../../01-plan/schema.md)).

```
전체 챕터 confirmed 상태 도달 → 사용자/가족이 출판 요청(publications.status='requested')
  → 조판 엔진: 하드커버용 PDF(CMYK 300DPI) 또는 ePub 생성 → MinIO 저장(storage_ref)
  → status='ready' → 사용자/가족에게 완료 알림
  → (하드커버) 인쇄 발주 — 배송·주문관리 세부는 Phase 3 이후 별도 확정
  → (ePub) 전자책 다운로드 링크 제공 → status='delivered'
```

### 2.7 온디바이스 상태 전이 & 폴백 정책 — 신규 v0.2

> 흐름도 3.1(상태머신)·3.3(유사도 폴백)·3.4(재질문 루프) 요약 (design-validator E-5).

```
Idle → Listening(웨이크워드 또는 마이크 버튼 탭 — M2 화면과 정합되도록 버튼 입력 우선, 웨이크워드는 Phase 2+ 검토)
  → VAD_Check → STT_Processing → IntentRouting → [Author|Care|Assist]Flow → LocalTTS → Idle

말벗돌봄 회상: 로컬 벡터 유사도가 임계치 미달 시 → 일반 공감 응답으로 폴백(구체 임계치는 Do 단계 튜닝)
비서 모드: 일정 파싱 결과 필수 정보(날짜/장소/목적) 미충족 시 → 재질문 루프
```

### 2.8 동기화 Diff/멱등성 처리 — 신규 v0.2

> 흐름도 4.2 "기존 청크와 Diff 비교" 반영 (design-validator E-6) — 재동기화 시 중복 청크 생성 방지.

```
업로드 수신 → 기존 conversation_chunks와 raw_audio_ref/체크섬 비교
  → 신규/변경분만 임베딩+Vector DB Upsert 진행, 동일분은 스킵
```

### 2.9 온보딩·가족 페어링 흐름 — 신규 v0.2

> 흐름도 5.1, 3.6(프로비저닝) 반영 (design-validator E-7). 엔티티: `invitations`([schema.md §3.16](../../01-plan/schema.md)).

```
스마트폰 최초 수령 → 설치모드 자동분기(§9 참조) → 초기설정(이름·Wi-Fi 등록)
  → 개인정보 수집 동의(consent_logs) → 가족 계정 웹 콘솔 초대(invitations 생성·토큰 발송)
  → 가족이 초대 수락(status='accepted') → 최초 Wi-Fi 동기화 → 첫 구술 인터뷰 시작
```

> **구현 상태 (v0.25)**: 서버측 consent 모듈 완료. **모바일 온보딩 화면 흐름 구현** — `presentation/onboarding/OnboardingScreen.kt`가 상태 호이스팅(sealed `OnboardingStep` + `when`, nav 프레임워크 미도입 결정)으로 이름 입력 → 개인정보 수집 동의 → 서버 3연쇄 → 완료. `onboarding/OnboardingCoordinator.kt`가 `createUser` → `POST /devices`(토큰·install_mode 발급) → `recordConsent(data_collection, granted=true)` 순으로 호출한다(동의 기록은 X-Device-Token이 필요해 기기 등록 뒤에 오지만, UI상 동의 화면이 먼저라 "수집 전 동의"는 지켜짐). `actor`(self/proxy)는 `granted_by` 유무에서 파생 — CTO 검토 B2가 권고한 명시적 enum(self/proxy/**legal_guardian**)·`data_subject` RBAC 행은 성년후견 대리동의 법적 근거가 법무 검토 대기라 미도입([decisions.md #12](../../01-plan/decisions/silveryarn-platform.decisions.md)).
>
> **구현 상태 (v0.28)**: 앱 시작 게이트 완성. `presentation/AppEntry.kt`가 `device_state` 조회로 시작 목적지를 정한다 — `device_id`가 있으면(온보딩 3연쇄 완료분) **온보딩·최초 동기화를 건너뛰고 바로 홈**, 없으면 온보딩 → **최초 Wi-Fi 동기화 화면**(`presentation/sync/FirstSyncScreen.kt` — 위 흐름의 "최초 Wi-Fi 동기화" 단계, `sync/SyncRunner.kt`를 1회 실행해 자서전 스냅샷·질문 큐·일정을 로컬 캐시에 채움, 실패 시 "건너뛰기"로 오프라인 진입 가능) → 홈. `install_mode` 분기(§9.3): `MainActivity`가 확정 모드를 받아 `installmode/KioskController.kt`로 `kiosk`면 lockTask 진입(decisions.md #6 — Device Owner가 아니면 조용히 무시). 동기화 절차 본체는 `SyncWorker.doWork()`에서 `SyncRunner`로 분리(Worker·최초 동기화 화면 공유). **"가족 계정 웹 콘솔 초대" 단계는 이 흐름에 미포함** — 갓 온보딩한 어르신 기기(Device Token)는 `POST /invitations`(2FA + family role) 호출 권한이 없어, 첫 가족 구성원 연결 경로는 별도 설계 결정 대기(웹 콘솔/admin 경로 또는 device-token 부트스트랩 엔드포인트).

### 2.10 에이전트 페르소나 정의 — 신규 v0.2

> 기획서 5.3 "동적 시스템 프롬프트" 및 UI/UX 화면설계서 확정 표시명 반영 (design-validator E-3).

| 에이전트 | 페르소나 | 표시명 | 톤 |
|---|---|---|---|
| AuthorAgent | 경청하는 인터뷰어 | *(미정 — 은빛이와 통일할지 별도 명칭 사용할지 결정 필요)* | 정중하고 호기심 있는 인터뷰어 |
| CareAgent | 사용자의 일생을 아는 친근한 오랜 벗 | **은빛이** (화면설계서 확정) | 다정하고 편안한 오랜 친구 |
| ScheduleAgent | 정확한 확인형 비서 | *(미정)* | 명료하고 신뢰감 있는 비서 |

### 2.11 말벗돌봄 Closed-Loop 통합 프로세스 (상세) — 신규 v0.3

> 사용자 제안 "하이브리드 지능형 라이프스토리 피드백 루프" 보고서(2026-09-06)를 검토·반영. §2.2 Data Flow의 고수준 흐름을 실행 가능한 수준까지 구체화한다. **원안의 서버측 생성 단계는 외부 GPT-4o/Claude로 제안되었으나, Zero External Data Egress 원칙(기획서 3.1 원칙2) 위반이라 온프레미스 vLLM으로 대체했다**([decisions.md #26](../../01-plan/decisions/silveryarn-platform.decisions.md)). Vector DB는 Qdrant 확정을 유지(#28)하고, 신규로 Neo4j 지식그래프를 채택(#29)했다.

**1단계 — 온디바이스 실시간 대화 및 로컬 영속화**
- 파이프라인: WebRTC VAD → 온디바이스 STT(Sherpa-ONNX 등 경량 엔진 후보) → 로컬 SQLite FTS5 키워드 검색(경량 RAG) → 온디바이스 SLM → 네이티브 TTS
- 원본 오디오는 16kHz PCM → **Ogg/Opus(16kbps)**로 실시간 압축 후 로컬 저장, 대화 턴은 로컬 SQLite(`session_id`/`turn_id`/`user_query`/`assistant_response`/`audio_path`/`sync_status`)에 기록

**2단계 — 비동기 업링크 동기화 (Edge → Cloud)**
- Android `WorkManager`가 Wi-Fi 연결+유휴/충전 상태를 감지해 백그라운드 워커 가동(기존 §2.2 "Wi-Fi 접속 감지"의 구체 구현)
- `sync_status='PENDING'` 음성(.opus)+대화로그를 `POST /api/v1/sync/upload`로 배치 전송(TLS 1.3)
- **[decisions.md #30]** 업로드 성공(200 OK) 확인 즉시 단말 원본 오디오 파일 삭제 — "최근 5일 캐시"(#9, 잠정)는 미동기화 상태의 보존 기간을 다루는 별개 축이며, 본 정책과 상충하지 않음

**3단계 — 서버 측 고정밀 분석 및 지식화 (전량 온프레미스)**
- STT 정밀 보정: 온프레미스 Whisper Large-v3로 재전사(사투리·고유명사 보정) — 기존 "고정밀 STT 재전사"(§2.2)의 구체 모델명
- 지식 추출: 온프레미스 vLLM으로 인물(Person)·연도(Time)·사건(Event)·감정(Emotion) 엔티티를 구조화 추출(JSON)
- 관계·타임라인은 **Neo4j 지식그래프**에 노드/엣지로 적재, 원문 청크는 **Qdrant**에 BGE-M3 임베딩으로 색인 (하이브리드 서치는 §2.4 그대로)
- 챕터 초안 윤문: 온프레미스 vLLM이 구술체를 문어체로 정제해 해당 챕터에 `draft`/`in_review` 상태로 저장 → 가족 웹 감수([workflow-diagrams.md §7](../workflow-diagrams.md), `chapter_revisions` 생성은 감수 시점에만) *(v0.6: §2.8은 동기화 Diff/멱등성 절이라 오참조였던 것을 정정, L-5)*
- **Critic Agent 갭 분석**: 서버 측 평가 에이전트가 서사 완성도를 Fact/Emotion/Relation/Reflection 4대 축으로 채점, 부족 영역(예: "특정 시기의 감정 결손")을 식별해 `questions`에 맞춤형 심층 질문(Top-3)을 생성 — 기존 §2.1 "질문 이력 대조·신규 회고 질문 생성"의 구체화

> **구현 상태 (v0.32)**: `questions`에 **생성 경로**가 생겼다(이전엔 read-only 큐). 업로드 파이프라인이 챕터 갱신 직후 `QuestionService.generate_followups()`를 best-effort로 호출 → `LLMClient.critique_and_generate_questions(chapter_body, latest_transcript, 기존_미답변_질문들)`(vLLM, `_CRITIC_SYSTEM_PROMPT`)이 4축 채점 후 질문 `[{text, type}]` Top-3을 반환, `questions` 큐에 `linked_chapter_id`와 함께 삽입. **큐 범람 방지**: 미답변 질문이 8개 이상이면 생성 스킵(기획서 4장 "한 번에 하나씩"), 기존 질문과 텍스트 중복(공백·대소문자 무시)이면 버림, 알 수 없는 `type`은 버림(코드가 임의 보정 안 함). `GET /sync/download`의 `priority_questions`가 이 큐를 그대로 내려보낸다 → §2.11 6단계 "진화된 재대화"의 재료. **4축 점수 자체를 저장·노출하는 경로는 미구현**(질문 생성에만 사용).

**4단계 — 온디바이스 맞춤형 경량화 패키징 (Compaction Engine)**
- 서버 확정 챕터 요약·핵심 키워드를 온디바이스 SQLite FTS5 테이블용 차분 데이터로 컴파일 (§2.4 "경량화 스냅샷 생성"의 구체 산출물)
- 다음 대화용 "단기 압축 기억(Short-term Compressed Persona)" JSON 룰셋 생성 — §2.10 페르소나 정의와 연동

> **구현 상태 (v0.31)**: 챕터 요약·키워드 부분 구현. 업로드 파이프라인(`upload_pipeline_service`)이 `save_draft` 직후 `ChapterService.compact_chapter()`를 best-effort로 호출한다 — `LLMClient.compact_chapter(body_text)`(vLLM, `_COMPACT_SYSTEM_PROMPT`)가 `{summary, keywords}` JSON을 반환하고 `chapters.compaction_summary`/`compaction_keywords`/`compacted_version`에 저장(마이그레이션 0007). `compacted_version != version`이면 stale로 보고 다음 턴에 재계산. `GET /sync/download`의 `chapter_updates.summary`/`keywords`가 이 값을 그대로 내려보내고, 아직 요약 안 된 챕터는 `body_text` 앞 200자로 임시 대체(이전엔 원문 전체/빈 배열). **"단기 압축 기억 JSON 룰셋"(페르소나, §2.10 연동)은 미구현** — 온디바이스 SLM/페르소나 배포 경로가 확정되면. **v0.39**: `POST /chapters/{id}/review` 승인(confirmed) 시에도 `compact_chapter()`(force=False)를 한 번 더 호출한다(gap-analysis-2026-09-11 G11 후속 #3) — 감수는 `body_text`/`version`을 바꾸지 않으므로 평소엔 재조회만 하고 끝나는 안전망이고, `save_draft` 시점 압축이 vLLM 장애로 실패했던 경우에만 확정 시점에 재시도한다. 실패해도 승인 자체는 이미 커밋된 상태를 그대로 반환(best-effort).

**5단계 — 하향 동기화 및 반영, 6단계 — 진화된 재대화**
- `GET /api/v1/sync/download` 응답 예시는 §4.3 참조. 로컬 SQLite에 Upsert(FTS5 인덱스, 우선순위 질문, 일정)되며, 다음 대화에서 온디바이스 SLM이 최신 맥락으로 더 깊은 꼬리질문을 구성한다.

> **아키텍처 자체는 신규가 아니다** — 위 6단계는 §2.2(Data Flow)·§2.4(RAG)·§2.1(작가엔진)의 고수준 흐름을 구현 기술 수준(Opus/WorkManager/Whisper Large-v3/Neo4j/Critic Agent/Compaction Engine)까지 구체화한 것이며, 기존 결정과 모순되지 않는다.

### 2.12 말벗돌봄 실시간 대화 파이프라인 (Latency-Optimized) — 신규 v0.4

> 사용자 제안 "저사양 실시간 대화 프로세스" 보고서(2026-09-06) 반영. 저사양·재활용 단말(키오스크 모드, RAM 4GB급)에서 끊김 없는 응답을 위한 온디바이스 8단계 파이프라인을 §2.7(온디바이스 상태전이)의 구체화로 명시한다. **아래 지연시간·메모리 수치는 제안자의 설계 목표치이며, 구체 라이브러리(Sherpa-ONNX 등)와 함께 실기기 벤치마크(#27) 전까지는 미검증 추정값이다.**

```
① VAD 감지(WebRTC VAD, 800ms 묵음 윈도우로 발화 종료 확정)
  → ② 온디바이스 STT 스트리밍 디코딩 (청크 단위 누적 처리)
  → ③ 키워드 추출 & 의도분류 (경량 룰/정규식)
  → ④ SQLite FTS5(BM25) 키워드 검색 — 임베딩 연산 없이 자서전 청크 인출 ([decisions.md #32](../../01-plan/decisions/silveryarn-platform.decisions.md))
  → ⑤ 동적 프롬프트 합성 (페르소나 지침 + 회상 기억 + 발화, Context 1,024 토큰 제한)
  → ⑥ SLM 스트리밍 추론 — 문장 종결부호(.?!\n) 감지 시 즉시 문장 단위 분할
  → ⑦ 문장 단위 TTS 파이프라이닝 — 전체 응답 완성을 기다리지 않고 첫 문장 즉시 합성(QUEUE_ADD)
  → ⑧ 로컬 DB 영속화 — 발화 텍스트·참조 챕터ID·응답소요시간(ms) 기록
```

**핵심 최적화 기법 (구조 확정, [decisions.md #31](../../01-plan/decisions/silveryarn-platform.decisions.md))**:
- Zero-Neural RAG: 온디바이스 임베딩 모델을 상주시키지 않고 FTS5 키워드검색만 사용 — RAM 절감
- 문장 단위 스트리밍(Sentence-Pipelining): SLM 토큰 생성 중 문장 경계에서 즉시 TTS로 바이패스 → 체감 응답속도 단축
- 안드로이드 Native TTS `QUEUE_ADD`로 문장을 이어붙여 끊김 없는 발화 재생

**메모리 예산 목표치 (제안, RAM 4GB급 단말 기준 — 벤치마크 검증 대기)**

| 모듈 | 목표 RAM | 비고 |
|---|---:|---|
| VAD (WebRTC VAD) | < 1MB | 후보 |
| STT (Sherpa-ONNX 등 후보, INT8) | ~95MB | 후보 |
| 로컬 RAG (SQLite FTS5) | ~0MB | OS 파일 캐시 공유 |
| SLM (Qwen2.5-0.5B 등 후보, Q4 양자화) | ~680MB | Context+KV캐시 포함, 벤치마크 후보(#27) |
| TTS (Android 네이티브) | ~0MB | 시스템 서비스 |
| 앱 런타임(UI·Room·코루틴) | ~75MB | |
| **합계(목표)** | **~850MB** | 4GB 단말 대비 안전마진 확보 목표 |

> 온디바이스 로컬 SQLite 스키마 초안(`autobiography_fts` FTS5 가상테이블 등)은 [`mobile-schema.md`](../../01-plan/mobile-schema.md) 참조 ([decisions.md #33](../../01-plan/decisions/silveryarn-platform.decisions.md)).

---

## 3. Data Model

> **정식 스키마는 [`docs/01-plan/schema.md`](../../01-plan/schema.md)(v1.3, 17개 엔티티)가 SoR이다.** 아래 TypeScript는 서버·웹 개발자를 위한 요약 참고용이며, 신규 컬럼 추가 시 schema.md를 먼저 갱신한 뒤 이 절을 동기화한다. (design-validator D-1~D-3 반영: `meta_people`을 배열로, enum을 영문으로 통일)

### 3.1 Entity Definition (요약 — 상세는 schema.md)

```typescript
interface User {
  id: string;
  name: string;
  birthDate?: string;          // ISO date — v1.1: birthYear에서 변경
  primaryDeviceId?: string;
  createdAt: string;            // v0.9 신규 — 실제 UserResponse에 이미 있던 필드 보강(SoR 원칙 2), apps/admin 사용자 목록 화면의 정렬 기준
  updatedAt: string;            // v0.9 신규
}

interface FamilyMember {
  id: string;
  userId: string;
  role: "family" | "caregiver" | "social_worker" | "admin";
  name: string;
  contact: string;
  twoFactorEnabled: boolean;
}

interface Device {
  id: string;
  displayId: string;           // v1.1 신규 — 표시용 ID (예: "MB-1042")
  modelName?: string;          // v1.1 신규
  userId: string;
  ramGb: number;
  androidVersion: string;
  installMode: "kiosk" | "normal";
  aiTops?: number;             // v0.7 신규 — schema.md §5 ai_tops(NPU 성능) 누락 보강, apps/admin 스캐폴딩 중 발견
  slmModelVersion?: string;    // v1.3 신규 — 2차 검증 M-3
  promptPackVersion?: string;  // v1.3 신규
  installedAt: string;
  lastSyncAt?: string;         // v0.7 신규 — 실제 devices 응답(core_service)에 이미 있던 필드 보강
}

interface Chapter {
  id: string;
  userId: string;
  chapterNo: number;           // v1.1 신규
  title: string;               // v1.1 신규
  period: "childhood" | "youth" | "adulthood" | "present";  // v1.1: 영문으로 변경, 표시명은 schema.md §7
  bodyText: string;
  status: "draft" | "in_review" | "rejected" | "confirmed";  // v1.1: rejected 추가
  version: number;
  updatedAt: string;            // v0.6 신규 — 3차 검증 L-11
  // v0.27(Check): `createdAt` 제거 — `chapters` 테이블/ChapterModel/ChapterResponse/schema.md DDL 어디에도
  //   없는 필드였다(v0.6 L-11에서 추가됐으나 구현 미반영). 챕터는 sync 파이프라인 산출물이고 `updatedAt`이
  //   이미 증분 다운로드 워터마크라 `createdAt` 수요 없음. SoR 원칙 1(코드 우선).
}

interface ChapterRevision {    // v1.1 신규
  id: string;
  chapterId: string;
  version: number;
  bodyTextSnapshot: string;    // 2차 검증 L-12 반영 — 누락돼 있던 필드
  reviewerId?: string;
  reviewComment?: string;
  action: "approved" | "rejected";
}

interface Photo {
  id: string;
  userId: string;
  uploaderType: "family" | "self";
  status: "pending_upload" | "uploaded";  // v0.15 신규 — schema.md v1.6엔 있었으나 이 인터페이스엔 누락돼 있던 것을 apps/web 사진 갤러리 구현 중 발견
  storageRef: string;
  caption?: string;            // v1.1 신규
  yearTag?: number;
  recallStatus: "pending" | "completed";
  placementStatus: "proposed" | "confirmed";  // v1.1 신규
  inlinePosition?: string;     // v1.1 신규
  linkedChunkId?: string;
  linkedChapterId?: string;
  qualityFlag: "ok" | "blurry" | "inappropriate" | "unreviewed";  // 2차 검증 L-12 반영
  width?: number; height?: number; fileSizeKb?: number; mimeType?: string;  // v1.1 신규
  uploadedAt: string;           // v0.6 신규 — 3차 검증 L-11
  viewUrl: string | null;       // v0.15 신규 — MinIO presigned GET URL(15분 만료), status가 uploaded일 때만 존재. storageRef는 내부 오브젝트 키라 브라우저가 직접 못 열어서 추가
}

interface PhotoRequest {       // v1.1 신규
  id: string;
  userId: string;
  requestedBy?: string;
  message?: string;
  status: "pending" | "fulfilled" | "dismissed";
  createdAt: string;            // v0.16 신규 — 실 응답엔 있었으나 이 인터페이스엔 누락돼 있던 것을 apps/web 사진 요청 화면 구현 중 발견
  fulfilledAt?: string;         // v0.16 신규
}

interface ConversationChunk {
  id: string;
  userId: string;
  rawAudioRef: string;
  transcriptOnDevice: string;
  transcriptServer?: string;
  meta: { period?: string; people?: string[]; place?: string; emotion?: string; prosody?: Record<string, unknown> };
  linkedPhotoId?: string;
  embeddingId?: string;
  graphNodeRef?: string;        // v1.2 신규 — Neo4j 지식그래프 노드 참조
  sessionId?: string;           // v1.3 신규 — 온디바이스 대화 세션 식별자
  turnId?: number;              // v1.3 신규
  mode?: "author" | "care" | "assist";  // v1.3 신규
  assistantResponse?: string;   // v1.3 신규 — 2차 검증 H-2, PII·암호화대상
}

interface Question {
  id: string;
  userId: string;
  linkedChapterId?: string;    // v1.1 신규
  text: string;
  type: "new_topic" | "follow_up";
  answered: boolean;
}

interface ScheduleItem {
  id: string;
  userId: string;
  kind: "appointment" | "medication";
  description?: string;
  location?: string;           // v1.1 신규
  recurrence?: string;         // v1.1 신규
  dueAt: string;
  status: "pending" | "confirmed" | "missed" | "declined";
  remindCount: number;         // v1.1 신규
  declineReason?: string;      // v1.1 신규
  nextRemindAt?: string;       // v0.6 신규 — 3차 검증 L-11
  respondedAt?: string;        // v0.6 신규 — 3차 검증 L-11
}

interface EmotionAlert {
  id: string;
  userId: string;
  score: number;
  triggeredAt: string;
  acknowledgedBy?: string;
  closedAt?: string;
}

interface EmotionScore {       // v1.1 신규
  id: string;
  userId: string;
  recordedDate: string;
  score: number;
  note?: string;
}

interface SyncSession {
  id: string;
  deviceId: string;
  direction: "upload" | "download";
  status: "success" | "failed" | "retrying";
  checksum: string;
  retryCount: number;          // 2차 검증 L-12 반영
  startedAt: string;           // v0.7 신규 — schema.md started_at 누락 보강, apps/admin 스캐폴딩 중 발견
  finishedAt?: string;         // v0.7 신규 — schema.md finished_at 누락 보강
}

interface ConsentLog {
  id: string;
  userId: string;
  consentType: "data_collection" | "external_tts_optin" | "external_llm_optin";
  granted: boolean;              // false = 철회 (동의/철회 모두 새 행으로 append)
  grantedBy?: string;            // 없으면 어르신 본인(self), 있으면 가족 대리(proxy)
  actor: "self" | "proxy";      // v0.18 신규 — grantedBy 유무에서 서버가 파생(CTO B2). 저장 컬럼 아님
  grantedAt: string;            // v0.18 신규 — 실 응답엔 있었으나 이 인터페이스에 누락돼 있던 것을 consent 모듈 구현 중 발견
}

interface NotificationSetting {  // v1.1 신규
  id: string;
  familyMemberId: string;
  channel: "sms" | "email" | "push";
  receivesEmotionAlerts: boolean;
  receivesChapterUpdates: boolean;
  receivesSyncIssues: boolean;
}

interface Invitation {          // v1.1 신규
  id: string;
  userId: string;
  invitedBy?: string;
  contact: string;
  role: FamilyMember["role"];
  token: string;
  status: "pending" | "accepted" | "expired";
  expiresAt: string;            // 2차 검증 L-12 반영
}

interface Publication {         // v1.1 신규
  id: string;
  userId: string;
  format: "hardcover_pdf" | "epub";
  status: "requested" | "processing" | "ready" | "delivered";
  storageRef?: string;
}
```

### 3.2 Entity Relationships

전체 시각 ERD는 [erd.md](../../01-plan/erd.md)를 참조(도메인별 3분할 + 속성·카디널리티 포함). 핵심 관계 요약:

```
[User] 1─N [Device]─N [SyncSession]     [User] 1─N [Chapter]─N [ChapterRevision]
   │                                              │
   ├─N [FamilyMember]─N [NotificationSetting]     ├─N [Photo]─0..1─[ConversationChunk]
   │                                              └─N [Question]
   ├─N [ConversationChunk]
   ├─N [ScheduleItem]           ├─N [PhotoRequest]      ├─N [EmotionAlert]
   ├─N [EmotionScore]           ├─N [ConsentLog]        ├─N [Invitation]
   └─N [Publication]
```

### 3.3 Database Schema

온프레미스 PostgreSQL 채택 확정(기획서 3.3). 정식 DDL은 [`docs/01-plan/schema.md`](../../01-plan/schema.md) §5 참조 (17개 테이블, 인덱스 포함).

---

## 4. API Specification

> 서버 프레임워크는 **Python/FastAPI 확정**([decisions.md #15](../../01-plan/decisions/silveryarn-platform.decisions.md)), REST 기반. bkend.ai BaaS 패턴은 해당 없음. API는 `/api/v1` 프리픽스로 버전을 관리하고, 리소스는 소유자(`users`) 하위로 중첩한다(design-validator F-3 반영). 상세 요청/응답 스펙은 Do 단계에서 OpenAPI로 확정한다.

### 4.1 표준 응답 포맷 (신규 v0.2, design-validator F-4)

```json
// 단건/성공
{ "data": { } }

// 목록(페이지네이션)
{ "data": [ ], "pagination": { "page": 1, "pageSize": 20, "total": 42 } }

// 에러
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} } }
```

**표준 에러 코드**: `VALIDATION_ERROR`(400) · `UNAUTHORIZED`(401) · `FORBIDDEN`(403) · `NOT_FOUND`(404) · `CONFLICT`(409) · `RATE_LIMITED`(429) · `PAYLOAD_TOO_LARGE`(413) · `SYNC_CHECKSUM_MISMATCH`(422, §6.2) · `INTERNAL_ERROR`(500) *(v0.6: 429/413 추가, [sync-contract.md §6](../sync-contract.md#6-표준-에러-코드-추가분))*

**필드 케이싱**: 서버 wire format은 **snake_case**로 통일([decisions.md #20](../../01-plan/decisions/silveryarn-platform.decisions.md)) — 웹(TS)·모바일(Kotlin)에서 각 스택 컨벤션으로 변환.

### 4.2 Endpoint List (초안)

> **리소스 중첩 규칙(F-3)**: 리소스는 원칙적으로 소유자(`users`) 하위로 중첩한다. 단, ① 업로드 트리거·액션성 엔드포인트(`/sync/upload`, `/photos/upload-url`, `/chapters/{id}/review`)와 ② 사전에 소유자를 특정할 수 없는 전역 생성 엔드포인트(`/invitations`, `/photo-requests`)는 예외로 중첩하지 않는다 — 3차 검증 M-8.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | /api/v1/sync/upload | 원본 음성+1차 전사+신규 사진 업로드 — **202 Accepted, 비동기 처리** ([sync-contract.md §2](../sync-contract.md#2-비동기-처리-계약-be-b1)) | Device Token |
| GET | /api/v1/sync/sessions/{sessionId} | 업로드 작업 상태 조회 (신규, [sync-contract.md §2.2](../sync-contract.md#22-작업-상태-조회-신규-엔드포인트)) | Device Token |
| GET | /api/v1/sync/sessions?deviceId={deviceId}&status={status}&page={page}&pageSize={pageSize} | 동기화 이력 조회, 페이지네이션 — apps/admin 동기화 모니터링 화면용(신규 0.7, deviceId 선택·페이지네이션·status 필터로 확장 0.10). deviceId를 생략하면 전체 기기 통합 모니터링. 응답 항목에 deviceDisplayId(0.11, devices 모듈에서 조합해 붙임 — SyncSession 엔티티 컬럼은 아님) 포함. 위 항목(기기 자신의 폴링용, Device Token)과 인가모델이 달라 별도 엔드포인트로 분리 | Admin |
| GET | /api/v1/sync/download?deviceId={deviceId}&since={syncVersion} | 최신 자서전·RAG 스냅샷·사진·질문목록 다운로드 — `since` 지정 시 증분만 반환. `deviceId`는 실제 구현 중 발견해 신규 추가한 필수 파라미터(0.14, [sync-contract.md §5](../sync-contract.md#5-증분-다운로드-be-b4)) | Device Token |
| GET | /api/v1/users/{userId}/chapters | 챕터 목록/본문 조회 | 2FA + Role |
| POST | /api/v1/chapters/{id}/review | 감수 승인/반려 (`chapter_revisions` 생성) | 2FA + Role(family) |
| GET | /api/v1/users/{userId}/photos | 사진 목록 조회 | 2FA + Role |
| POST | /api/v1/photos/upload-url | 사진 업로드용 Presigned URL 발급 (신규, [sync-contract.md §4](../sync-contract.md#4-사진-업로드--presigned-url-흐름-be-b2)) | 2FA + Role(family) 또는 Device Token |
| POST | /api/v1/photos/{id}/complete | 사진 업로드 완료 확인 (신규) | 2FA + Role(family) 또는 Device Token |
| POST | /api/v1/photo-requests | 가족→당사자 사진 추가 요청 | 2FA + Role(family) |
| GET | /api/v1/users/{userId}/photo-requests | 사진 추가 요청 목록 조회(신규 0.13, 스캐폴딩 시점 추가 — invitations 모듈과 동일 이유: 만들기만 하고 볼 방법이 없으면 WU3→WF3 루프가 끝나지 않음) | 2FA + Role |
| POST | /api/v1/photo-requests/{id}/dismiss | 사진 추가 요청 닫기(신규 0.13) — 충족(fulfilled)은 이 엔드포인트가 아니라 POST /photos/{id}/complete가 자동 처리 | 2FA + Role |
| GET | /api/v1/users/{userId}/emotion-scores | 일별 정서 점수 추이 조회 | 2FA + Role |
| GET | /api/v1/users/{userId}/emotion-alerts | 정서 알림 이력 | 2FA + Role |
| GET | /api/v1/family-members/{id}/notification-settings | 알림 수신 설정 조회 (구현 v0.22) | 2FA + 본인/admin |
| PUT | /api/v1/family-members/{id}/notification-settings | 알림 수신 채널·항목 설정 — 이 구성원의 설정 전체 교체(delete→insert). `receives_emotion_alerts` 기본 opt-out(CTO B1). 구현 v0.22 | 2FA + 본인/admin |
| POST | /api/v1/invitations | 가족 구성원 초대 | 2FA + Role(family) |
| POST | /api/v1/users/{userId}/publications | 인쇄/출판 요청 | 2FA + Role |
| POST | /api/v1/devices | 설치 시점 1회 기기 등록(F-3 예외, 부트스트랩 — 인증 없음). 응답에 **Device Token 1회 발급**(v0.19, decisions.md #47 — 이후 `/sync/*`는 이 토큰을 `X-Device-Token`으로 제시) | 없음(부트스트랩) |
| GET | /api/v1/users/{userId}/devices | 기기 사양·설치모드 조회 (관리자, 조회 전용) — *(v0.6: `/devices/{userId}` → 소유자 중첩 규칙에 맞게 정정, M-8)* | Admin (role 강제, v0.19) |
| GET | /api/v1/users?page={page}&pageSize={pageSize}&name={name} | 전체 사용자 목록 조회, 페이지네이션(신규 0.8) + 이름 부분일치 검색(신규 0.12) — F-3 예외(사전에 소유자를 특정할 수 없는 전역 조회) | Admin |
| GET | /api/v1/users/{userId}/questions | 회고 질문 큐 조회 (L-12, 구현 v0.20 — `answered` 필터 옵션. sync/download의 `priority_questions`와 달리 필터 없이 큐 전체) | 2FA + Role |
| GET | /api/v1/users/{userId}/schedule-items | 일정/복약 목록 조회 (신규, L-12) | 2FA + Role |
| POST | /api/v1/users/{userId}/consent-logs | 개인정보 수집 동의/철회 1건 기록 (신규 0.18 — §2.9 온보딩 흐름이 이미 전제하던 '동의 기록' 경로가 §4.2에 없던 갭). 응답 `actor`(self/proxy) 파생 | 2FA + Role(family) 또는 Device Token |
| GET | /api/v1/users/{userId}/consent-logs | 동의 이력 조회 (신규, L-12) | 2FA + Role |
| GET | /api/v1/users/{userId}/consent-state | 유형별 현재 동의 상태(최신 행 기준) — 온보딩 완료 게이트·RBAC "동의 시" 조건용 (신규 0.18) | 2FA + Role |

> 구독/결제 엔드포인트는 스코프 아웃([decisions.md #18](../../01-plan/decisions/silveryarn-platform.decisions.md)) — 포함하지 않음.
> 동기화·업로드 관련 상세 계약(비동기 처리, 충돌정책, Presigned URL, 증분 다운로드)의 SoR은 [sync-contract.md](../sync-contract.md)이며, 이 표는 요약만 담는다.

### 4.3 Detailed Specification

세부 요청/응답 스펙(OpenAPI)은 Do 단계에서 확정. 아래는 `GET /api/v1/sync/download` 응답 예시(§2.11 Compaction Engine 산출물 — snake_case 확정 반영, [decisions.md #20](../../01-plan/decisions/silveryarn-platform.decisions.md)):

```json
{
  "data": {
    "sync_version": "sync_v20260906_02",
    "chapter_updates": [
      {
        "chapter_id": "b3f1...-uuid",
        "chapter_no": 2,
        "period": "youth",
        "keywords": ["1978년", "인천공장", "김반장", "월급"],
        "summary": "1978년 인천 기계공장 근무 시절 김 반장과의 갈등 및 극복기"
      }
    ],
    "priority_questions": [
      { "question_id": "q_...-uuid", "linked_chapter_id": "b3f1...-uuid", "text": "인천 공장 계실 때 첫 월급 타서 사모님께 어떤 선물을 하셨는지 기억나세요?", "type": "follow_up" }
    ],
    "schedule_items": [
      { "id": "s_...-uuid", "kind": "medication", "due_at": "2026-09-07T08:30:00+09:00", "description": "혈압약" }
    ]
  }
}
```

> `chapter_updates`는 온디바이스 SQLite FTS5 테이블 Upsert용 차분 데이터, `priority_questions`는 로컬 질문목록 큐 갱신용이다(§2.11 4단계).

---

## 5. UI/UX Design

> 전체 화면 스펙은 [`Plan/은빛실타래_UIUX_화면설계서.html`](../../../Plan/은빛실타래_UIUX_화면설계서.html)(v1.2)에 상세 정의되어 있음. 디자인 토큰(컬러/타이포)은 [`design-tokens.md`](../design-tokens.md) 참조(신규 v0.2, design-validator F-5).

### 5.1 Screen Inventory

> ✅ = apps/web·apps/mobile·apps/admin에 구현됨. 나머지는 미착수 또는 외부 결정 대기.

| 영역 | 화면 |
|---|---|
| 모바일앱(당사자) | 온보딩·동의 ✅, 홈·음성대화 ✅(M2 셸 + 하단 탭 4개, v0.38 — 마이크 세션 라우팅은 온디바이스 SLM 라우터 붙기 전까지 말벗돌봄 모드 고정), 자서전 작가모드 인터뷰(스텁), 말벗돌봄 대화(스텁), 비서모드 일정·복약(스텁), 설정·동기화 상태(최초 동기화 ✅), 사진 추가하기 |
| 웹·자서전 사용자 | **로그인 ✅**(`/login` — Keycloak SSO, v0.34), 자서전 뷰어 ✅, 사진·타임라인 갤러리 ✅, ~~구독·결제 관리~~(스코프 아웃, decisions.md #18), 계정 설정 |
| 웹·가족 | 가족 대시보드(오늘의 기억 리포트) ✅(`(family)/dashboard`, v0.37 — 정서 항목은 안내문구로 대체), 원고 감수·대조편집 ✅, 사진 업로드·타임라인 배치(사진 요청 ✅), 정서 모니터링 상세(⚖️ 정서 파이프라인 OFF), 알림·가족구성원 설정 ✅(`(family)/notification-settings`) |
| 웹·관리자 | 관리자 대시보드, 사용자 관리 ✅, Wi-Fi 동기화 모니터링 ✅, 정서 알림 이력 관리(⚖️ OFF), 시스템 설정·리소스 모니터링, 기기 관리 ✅ |

> **인증 상태**: **apps/web·apps/admin 모두 Keycloak 로그인 연동 완료**(Auth.js, decisions #49) — 모든 웹 화면이 실 백엔드(§7.4)에 실 Bearer 토큰으로 동작한다. 두 앱이 같은 `silveryarn-web` 클라이언트(web 3000 / admin 3001).

### 5.2 Page UI Checklist

> 원본 UI/UX 화면설계서에 화면별 상세 스펙(`spec-name` 단위)이 이미 존재하므로, 신규 체크리스트 재작성 대신 원본 문서를 SoR로 삼는다.

---

## 6. Error Handling

### 6.1 동기화 실패·충돌 처리 (프로세스흐름도 5.6절 기반)

| 상황 | 처리 |
|------|------|
| 업로드 실패 | 지수 백오프 재시도(최대 N회 — 횟수는 Do 단계에서 확정) |
| 다운로드 실패 | 재시도 |
| 체크섬 검증 실패 | 손상 데이터 폐기 후 재다운로드 요청 |
| 로컬-서버 버전 충돌 | **엔티티별로 상이** — 무차별 Server-Wins 아님. 상세 정책은 [sync-contract.md §3](../sync-contract.md#3-엔티티별-충돌정책-server-wins-전면적용-폐기) 참조 *(v0.6: CTO Enterprise B1/3차 검증 H-3 반영, 단일 Server-Wins 규칙 폐기)* |

### 6.2 표준 에러 코드

§4.1 참조.

---

## 7. Security Considerations

- [ ] DB 암호화(AES-256) 및 전송구간 암호화(TLS 1.3) — 온디바이스 로컬 캐시도 동일 수준. **PII 자유텍스트 컬럼의 앱 레이어 필드 암호화는 §7.3 참조(1차 구현 완료)**
- [ ] 웹 콘솔 2FA, 역할별 차등 열람 권한(가족/복지사/관리자) — §7.1 RBAC 매트릭스 참조
- [ ] 외부 연계(3.4절) 시 PII 마스킹 전처리 + 동의 로그 필수, 미동의 시 전량 온프레미스 경로
- [ ] Wi-Fi 동기화는 등록된 신뢰 네트워크에서만 수행 — 등록 정보는 온디바이스 로컬 전용 저장([decisions.md #22](../../01-plan/decisions/silveryarn-platform.decisions.md))
- [ ] Device Owner Mode(COSU) 채택 확정([decisions.md #6](../../01-plan/decisions/silveryarn-platform.decisions.md)) — 단말 탈취·우회 방지 상세 구현은 Do 단계에서 검토
- [ ] **설치모드 판별 임계값(확정 수치)**: `ram_gb < 6 OR android_version <= '11'` → kiosk ([decisions.md #5](../../01-plan/decisions/silveryarn-platform.decisions.md), [schema.md §3.3](../../01-plan/schema.md)) — design-validator C-1 반영, 구현 기준 문서인 본 절에 수치 직접 명기

### 7.1 RBAC 권한 매트릭스 (신규 v0.2, design-validator E-8)

> 기획서 6장 "역할별 차등 권한" 요구를 구체화. 세부 조정은 Do 단계.
>
> **v0.24 구현 상태**: social_worker의 "동의 시" 열람은 그 동의를 표현할 consent 유형이 없고 CTO B2가 제3자제공 여부를 법무 질문으로 지목한 상태라, **fail-closed로 구현**했다 — 전용 consent 유형이 확정될 때까지 복지사는 어르신 데이터(챕터·사진·대화·일정) 조회에서 제외된다(정서 알림·본인 알림설정은 유지). `core/auth.py`의 `READ_ELDER_DATA_ROLES` = {family, caregiver, admin}.

| 리소스 | family | caregiver | social_worker | admin |
|---|:-:|:-:|:-:|:-:|
| 챕터 조회 | ✅ | ✅ | ⏸️(동의 시 — fail-closed, 미도입) | ✅ |
| 챕터 감수(승인/반려) | ✅ | ❌ | ❌ | ✅ |
| 사진 업로드 | ✅ | ✅ | ❌ | ✅ |
| 정서 알림 조회 | ✅ | ✅ | ✅ | ✅ |
| 정서 알림 확인(acknowledge) | ✅ | ✅ | ✅ | ✅ |
| 알림 수신 설정 변경 | ✅(본인 것만) | ✅(본인 것만) | ✅(본인 것만) | ✅ |
| 기기 관리(조회) | ❌ | ❌ | ❌ | ✅ |
| 사용자 관리 | ❌ | ❌ | ❌ | ✅ |
| 동기화 모니터링 | ❌ | ❌ | ❌ | ✅ |

### 7.2 백업 정책 (신규 v0.2, design-validator E-9)

기획서 6장 "JSON·마크다운 상시 백업" — 자서전 챕터(`chapters`, `chapter_revisions`)는 확정 시점마다 JSON/Markdown 스냅샷을 Object Storage(MinIO)에 별도 보관한다. 백업 주기·보존기간은 Do 단계에서 인프라 설계와 함께 확정.

> ⚠️ 백업 스냅샷도 `body_text`/`body_text_snapshot` 원문을 담으므로 §7.3의 암호화 대상이다 — MinIO 객체 자체를 SSE로 암호화하거나 스냅샷 생성 시 앱 레이어 암호문을 그대로 직렬화한다(Do 단계 구현 시 확정).

### 7.3 PII 필드 암호화 (신규 v0.17, Do 단계 — [decisions.md #45](../../01-plan/decisions/silveryarn-platform.decisions.md), CTO 검토 B4)

CTO 보안 검토 B4가 "스키마 결정, Do 단계 이연 불가"로 지목한 항목. `pgcrypto`는 미채택(키 유출·인덱스 불가)하고 **애플리케이션 레벨 필드 암호화 + 사용자별 DEK** 구조를 채택했다.

| 요소 | 1차 (v1.7) | 2차 (v1.11, 코드 반영 완료) | 3차 (예정) |
|---|---|---|---|
| 대상 컬럼 | `chapters.body_text`, `chapter_revisions.body_text_snapshot`, `conversation_chunks.{transcript_on_device, transcript_server, assistant_response}` | `family_members.contact`·`invitations.contact`(암호문 + `contact_bidx` HMAC), `users.birth_date`(DATE→VARCHAR 암호문). **`name`은 평문 유지 확정** (부분검색 UX, CTO B4도 최고위험 아님) | — |
| 방식 | Fernet(AES-128-CBC+HMAC), 토큰 접두 `pii.v1.` | 동일 + blind index = HMAC-SHA256(정규화값), 키는 KEK 첫 키에서 유도 | 결정적 KEK 회전 절차(`key_version`), Vault transit 엔진 |
| 키 | 사용자별 DEK(`user_encryption_keys`에 KEK 랩핑), KEK = env `PII_KEK`(임시) | 동일. blind index 키는 KEK 첫 키에서 유도(회전 시 백필 필요) | Vault 이전, blind index 키 정식 분리 |
| 경계 | repository 계층 투명 암복호화 (`core/crypto.py`) | 동일 (`family_member`·`invitation`·`user` repo에 `PiiFieldEncryptor` 주입) | — |

- **crypto-shredding**: 사용자 파기 = `user_encryption_keys` 행 삭제 → 그 사용자의 PII 자유텍스트 전량 복호화 불가. B3(보유기간·파기정책) 파기 수단 후보 — 법무 회신(원문 검토항목 5) 대기.
- **Qdrant 벡터**: B4가 "최고위험"으로 지목(embedding inversion). payload에 원문 미저장 원칙은 `upload_pipeline_service`에서 이미 준수(payload는 `user_id`만). 벡터 자체 격리·네트워크 통제는 인프라 설계 과제로 유지.
- **임시 검색 영향**: `transcript_server` 암호화로 `conversation_chunks` ILIKE 검색이 앱 레이어 복호화 필터로 바뀜(이미 rag-core 하이브리드 서치로 교체 예정이던 임시 메서드).
- **contact blind index 활용 (v1.11)**: `invitations`가 `contact_bidx`로 "같은 어르신 계정에 같은 연락처로 대기 중인 초대"를 막는다(중복 초대 방지). `family_members.contact_bidx`는 채우기만 하고 검색 메서드는 후속.

### 7.4 인증·인가 (신규 v0.19, Do 단계 — [decisions.md #47](../../01-plan/decisions/silveryarn-platform.decisions.md), CTO 검토 B5)

원본 프로세스흐름도 §4.1: 모든 요청은 게이트웨이에서 Keycloak SSO 인증/인가를 거친다. `core/auth.py` 스텁을 실 검증으로 교체했다. (v0.30) 순수 로직(`core/auth.py`)과 리포지토리 조립(`core_service/auth_deps.py`)을 분리 — 라우터는 `auth_deps`에서 인증 심볼을 가져온다.

| 주체 | 방식 | principal |
|---|---|---|
| 웹 콘솔 사용자(가족/복지사/관리자) | `Authorization: Bearer` — Keycloak 액세스 토큰 RS256 검증(JWKS 캐시, iss/aud/exp). `sub` → `family_members.keycloak_sub`(다중 행 가능) → `AuthContext(memberships, is_2fa)` | `AuthContext` |
| 모바일 기기 | `X-Device-Token` — `POST /devices` 응답으로 1회 발급, 서버는 SHA-256 해시만 보관(`device_credentials`). 검증 시 (기기 → 소속 어르신)까지 해석 | `DeviceIdentity` |

- **2FA**(기획서 6장 "웹 콘솔 접근 시 2단계 인증"): 토큰 `amr` claim으로 판정(`AUTH_2FA_AMR_VALUES`). 쓰기·감수 작업은 `require_2fa=True`.
- **인가(RBAC + IDOR 방지)**: `authorize_user_access(principal, target_user_id, allowed_roles, require_2fa)` — 대상 어르신에 대한 membership·role·2FA를 검사(admin은 우회, device는 소속 어르신만). §7.1 매트릭스 기준. **적용 범위**(v0.19 + v0.21): chapters(조회·감수)·photos(조회·업로드)·consent(전체)·schedule(조회·생성·응답)·conversation-chunks(조회)·users(`GET /users`=admin, `GET /users/{id}`=연결된 가족/admin)·devices(조회=admin)·sync(`/sessions` 목록=admin, device 엔드포인트는 device_id 일치)·**family-members**(조회·생성=family/admin+2FA, contact가 PII)·**invitations**(생성=family/admin+2FA, `invited_by`는 호출자 본인 구성원)·**photo-requests**(생성=family/admin, 조회·닫기=Device 또는 가족).
- **초대 수락 → 계정 연결**: `POST /invitations/{token}/accept`는 아직 family_member에 매핑 안 된 계정이라 `require_verified_subject`(토큰만 검증, membership 미확인)를 쓴다. 수락자 토큰 `sub`를 새 `family_members.keycloak_sub`에 박아넣어야 이후 `require_family`가 그 사람을 로그인시킬 수 있다(이게 없으면 수락 후에도 앱을 못 씀). `GET /invitations/{token}`은 계속 무인증(토큰 자체가 접근 권한).
- **social_worker fail-closed (v0.24)**: 복지사의 어르신 데이터 조회는 `READ_ELDER_DATA_ROLES`에서 제외(family/caregiver/admin만). RBAC §7.1의 "동의 시"를 표현할 전용 consent 유형이 없고 제3자제공 법무 판단 대기(CTO B2, decisions.md #12/#46 관련). 전용 유형 확정 시 그 동의 상태를 게이트로 복지사를 다시 포함.
- **미적용(후속)**: `emotion_alerts`/`emotion_scores` 엔드포인트(피처플래그 OFF).
- **감사로그**: `access_logs` — `main.py` HTTP 미들웨어가 `/api/v1/*` 요청 처리 후 best-effort 1행 적재(제8조).
- **fail closed**: `AUTH_ISSUER_URL` 미설정 시 웹 콘솔 인증이 요청에서 401(토큰 없음) 또는 500(토큰 있는데 verifier 미구성). 앱/워커 기동·CI(HTTP 미경유 단위 테스트)에는 영향 없음.
- **실 인프라 e2e 검증(v0.26, 2026-09-09)**: 로컬 Keycloak(`infra/keycloak/`, realm 자동 임포트)으로 `services/backend/scripts/e2e_keycloak_check.py` — JWKS RS256 검증·`sub`→`family_members` 매핑·`authorize_user_access`·social_worker fail-closed·2FA(`amr`) 게이팅 **9/9 PASS**. PII 암복호화·멱등성·access_logs는 `e2e_pii_auth_check.py`(17/17)·`e2e_http_smoke.py`(13/13).
- **웹 콘솔 로그인(v0.34~v0.35, decisions #49)**: apps/web·apps/admin **둘 다 Auth.js(NextAuth v5) + Keycloak provider**. `silveryarn-web`(public client) auth code flow + PKCE, realm `redirectUris`에 `localhost:3000/*`(web)·`localhost:3001/*`(admin). `lib/api/client.ts`가 `import "server-only"` — 서버에서만 실행되며 `auth()` 세션의 액세스 토큰을 백엔드 `Authorization: Bearer`로 전달(브라우저 노출 없음). web의 클라이언트 폼 제출은 Server Action(`features/*/actions.ts`) 경유; admin은 GET 전용이라 불필요. admin 화면은 백엔드 `require_roles(admin)`이 다시 검사(프론트는 유효 세션만). Next.js 16 `proxy.ts`(구 middleware)가 미로그인 요청을 `/login`으로. 양쪽 앱 로컬 실 flow 브라우저 검증(로그인→세션→실 Bearer로 조회·PUT→반영).
- **감수 서명자**: `POST /chapters/{id}/review`의 `reviewer_id`는 이제 토큰에서 파생(하위호환용 요청 필드는 유지하되 호출자 본인 구성원 id만 허용).

---

## 8. Test Plan

> 상세 L1~L3 테스트 시나리오는 Phase별 구현 착수 시 확정. 아래는 Design 단계에서 식별된 우선 검증 대상이다.

### 8.1 Test Scope

| Type | Target | Tool | Phase |
|------|--------|------|-------|
| 오프라인 시나리오 | 인터넷 차단 상태에서 3대 모드 응답 | 실기기/에뮬레이터 수동 QA | Do |
| 동기화 시나리오 | Wi-Fi 접속/차단 반복, 업/다운로드 재시도·체크섬, Diff 멱등성(§2.8) | 네트워크 장애 주입 | Do |
| 사진 회고 파이프라인 | 업로드→미회고 큐→회고 대화→챕터 인라인 편입(placement_status 전이 포함) | E2E 시나리오 | Do |
| 설치모드 분기 | RAM/OS 경계값 기기에서 키오스크/일반 분기 정확도 (§7 확정 수치 기준) | 실기기 매트릭스(부록A 3.3) | Do |
| 정서 모니터링 | emotion_scores 일별 기록, 임계치 초과 시 emotion_alerts 생성·알림 발송(§2.5) | E2E 시나리오 | Phase 2 (피처플래그 OFF — decisions.md #25, §11.2 step 6) |
| 출판 파이프라인 | 챕터 전체 confirmed → publications 요청 → PDF/ePub 생성(§2.6) | E2E 시나리오 | Phase 3 (§11.2 step 7) |

---

## 9. Clean Architecture

### 9.1 Layer Structure (Enterprise, On-Premise 변형)

> **v0.27 (Check 단계, SoR 원칙 1)**: 서버 Location 열을 실제 구현 구조로 교체했다. 첫 커밋을 6개
> 서비스가 아닌 **단일 모듈러 모놀리스**(`services/backend/`, decisions.md #44)로 찍었으므로 `services/{engine}/`
> 경로는 존재하지 않는다. 4계층 패턴은 이제 도메인 모듈(`modules/{name}/`) 단위로 반복된다 — structure.md v1.4 참조.

| Layer | Responsibility | Location |
|-------|---------------|----------|
| **모바일 Presentation** | 음성 UI, 대화 화면, 사진 업로드 UI | `apps/mobile/.../presentation/`, `.../onboarding/` |
| **모바일 On-Device AI** | VAD·STT·SLM·TTS, 로컬 라우터 | `apps/mobile/.../ondevice/` |
| **모바일 Infrastructure** | 로컬 SQLite(FTS5, Phase 1 기본 — [mobile-schema.md](../../01-plan/mobile-schema.md)), 경량 VectorDB(Phase 2+, 고사양 단말 한정), 동기화 클라이언트 | `apps/mobile/.../local/`, `.../sync/` |
| **서버 Presentation** | FastAPI 라우터(모듈별 `api/v1/`), `main.py`(api 프로세스), 웹 콘솔 | `services/backend/src/core_service/modules/{name}/api/`, `apps/web/`, `apps/admin/` |
| **서버 Application** | 모듈별 유스케이스(서비스 클래스), arq 워커(`worker.py`) | `services/backend/src/core_service/modules/{name}/application/` |
| **서버 Domain** | 모듈별 Entity·비즈니스 규칙(챕터 귀속, 사진 인라인 규칙). 2+ 모듈 공유 값 객체(enum)는 공유 커널 | `services/backend/src/core_service/modules/{name}/domain/`, 공유분은 `core_service/shared/` |
| **서버 Infrastructure** | Qdrant/Neo4j/PostgreSQL/MinIO 연동, vLLM 클라이언트, ORM 모델·리포지토리 | `services/backend/src/core_service/modules/{name}/infrastructure/`, `core_service/core/clients/` |

### 9.2 Dependency Rules

```
Presentation ──→ Application ──→ Domain ←── Infrastructure
Domain은 외부 의존성 없이 독립 (순수 엔티티·규칙만)
Application은 Domain에 항상 의존하며, Infrastructure는 Domain이 정의한
인터페이스(포트)를 구현해 Application에 주입된다 (의존성 역전) — structure.md §6 참조
```

### 9.3 설치모드 자동분기(참고 — 기획서 3.7·decisions.md #5,#6)

키오스크(RAM<6GB 또는 Android≤11) / 일반 앱은 설치·잠금 방식만 다르고 3대 운영 모드 기능은 완전히 동일하다. 구현 세부는 `apps/mobile/installmode/`([structure.md](../../01-plan/structure.md) 참조).

---

## 10. Coding Convention Reference

> Phase 2 완료 — 정식 컨벤션은 [`CONVENTIONS.md`](../../../CONVENTIONS.md) 및 [`docs/01-plan/naming.md`](../../01-plan/naming.md), [`structure.md`](../../01-plan/structure.md) 참조. 서버는 Python(FastAPI) 기준 PEP8+snake_case, 모바일은 Android 네이티브 Kotlin, 웹 콘솔은 Next.js/TypeScript로 확정.

---

## 11. Implementation Guide

> ⚠️ **CTO팀 아키텍처 리뷰 권고(Enterprise B3)**: 6개 서비스 구조를 첫 스캐폴딩 커밋에서 그대로 6개 독립 배포 단위로 찍지 말 것. Phase 1은 **모듈러 모놀리스 2프로세스(api / worker)**로 시작하고, 폴더 경계만 유지하며 import-linter로 엔진 간 직접 참조를 CI에서 차단하는 방식을 권장한다. 실제 서비스 분리는 GPU 스케일 독립이 필요해지는 시점(rag-core 등)에 재검토([cto-review](../cto-review-2026-09-05.md#1-enterprise-architect--아키텍처-전략-심사) B3 참조).
>
> **v0.27 (Check 단계) — 구현 반영**: 위 권고대로 `services/backend/` 단일 모듈러 모놀리스로 구현됨(decisions.md #44). 아래 트리는 실제 구조다.
>
> **v0.29 — import-linter 도입**: `pyproject.toml [tool.importlinter]`에 contract 4개 + CI(`ci.yml` backend job `lint-imports` 스텝). ① 12개 도메인 모듈 각각 `api → application → infrastructure → domain` 4계층(역방향 import 금지), ② `modules.*.domain`의 프레임워크(fastapi/sqlalchemy/pydantic) 의존 금지, ③ `shared/`↛`modules`, ④ `core/`↛`modules`. 모듈은 서로의 `application`/`domain`/`deps`만 참조하고 `infrastructure`/`api`는 직접 참조하지 않는다.
>
> **v0.30 — `core/auth.py` 순수화**: contract ④의 예외였던 "`auth.py`가 principal 해석에 `family_members`/`devices` 리포지토리를 지연 import" 2건을 제거했다. `core/auth.py`는 이제 순수(토큰 검증·인가 규칙·조회 포트 `FamilyMemberDirectory`/`DeviceTokenDirectory` Protocol만), 리포지토리와 엮는 FastAPI 의존성(`require_family`/`require_device`/`require_principal`/`require_roles`)은 `core_service/auth_deps.py`(최상위 조립 모듈, `main.py`/`model_registry`처럼 `modules` import 허용)로 이동. 라우터는 인증 심볼을 전부 `auth_deps`에서 가져온다. contract ④의 남은 예외는 `model_registry` 1건뿐. 실 인프라 e2e 17/17·13/13·9/9 재확인.

### 11.1 File Structure (실제 구현 — v0.27)

```
silveryarn/
├── apps/
│   ├── mobile/             # 온디바이스 앱 (Kotlin, 설치모드 자동분기 포함)
│   │   └── app/src/main/java/com/silveryarn/mobile/
│   │       ├── auth/ installmode/ local/ ondevice/ onboarding/ sync/
│   │       └── presentation/{assistant,author,care,onboarding,settings}/
│   ├── web/                # 자서전 사용자·가족 웹 콘솔 (Next.js App Router)
│   └── admin/              # 관리자 콘솔 (Next.js App Router)
├── services/
│   └── backend/            # ★ 단일 배포 단위 (모듈러 모놀리스, decisions.md #44)
│       ├── src/core_service/
│       │   ├── main.py            # api 프로세스 (FastAPI)
│       │   ├── worker.py          # worker 프로세스 (arq 잡 큐)
│       │   ├── core/              # 횡단 관심사: auth, crypto, db, queue, config,
│       │   │   ├── clients/       #   model_registry(전 ORM 모델 import), access_log
│       │   ├── shared/            # 공유 커널 — 2+ 모듈이 쓰는 enum 등 (domain_enums.py)
│       │   └── modules/{users,devices,author,care,schedule,sync,
│       │       consent,family_members,invitations,notifications,
│       │       photos,photo_requests}/
│       │       ├── api/v1/        # FastAPI 라우터
│       │       ├── application/   # 유스케이스 (서비스 클래스)
│       │       ├── domain/        # 엔티티·값 객체·규칙 (순수)
│       │       ├── infrastructure/# ORM 모델·리포지토리·외부 연동
│       │       └── deps.py        # 이 모듈의 DI 조립 (타 모듈은 이것만 import)
│       ├── migrations/versions/   # Alembic 0001~0007
│       ├── scripts/e2e_*.py       # 실 인프라 e2e (pii/http/keycloak)
│       └── tests/                 # Fake*Repository 기반 Application 계층 단위 테스트
├── infra/
│   ├── docker-compose.yml         # postgres/redis/qdrant/neo4j/minio/keycloak (port 9670~9678)
│   └── keycloak/import/           # 로컬 realm (--import-realm 자동)
├── docs/                          # PDCA 문서
└── Plan/                          # 원본 기획 산출물 (보존)
```

> `packages/py-common`·`services/{gateway,*-engine,rag-core,shared}`는 만들지 않았다 — 단일 모놀리스에서는 `core_service/shared/`(공유 커널)와 `core_service/core/`(횡단)로 충분. 물리 분리가 필요해지면 `modules/{name}/`을 통째로 옮긴다(structure.md §2).

### 11.2 Implementation Order

1. [x] Phase 1 스키마 확정 (`/phase-1-schema`) — schema.md v1.12, 서버 21개 테이블(도메인 17 + 부속 4), 마이그레이션 0001~0007
2. [x] Phase 2 컨벤션 확정 (`/phase-2-convention`)
3. [~] 온디바이스 오프라인 코어(STT/SLM/TTS) + 로컬 캐시 — 앱 셸·온보딩·앱시작게이트·sync 클라이언트·Room 스키마 구현, STT/SLM/TTS 런타임은 모델 선정(decisions.md #27) 대기
4. [x] Wi-Fi 배치 동기화 기본 흐름 (업/다운로드, 재시도, 체크섬, Diff 멱등성) — sync-contract.md v0.6, 업로드 멱등성 3계층
5. [x] 자서전 작가 엔진 + 웹 콘솔 감수 흐름 (Phase 1 MVP) — author 모듈(chapters/questions), `POST /chapters/{id}/review`, apps/web 감수 화면. **§2.11 서버측 클로즈드 루프**: Compaction Engine(4단계, 요약·키워드 — PR #15)·Critic Agent(3단계, `questions` 생성 — PR #16) 구현. Compaction Engine의 페르소나 JSON 룰셋(§2.10 연동)은 미구현
6. [ ] 말벗돌봄 엔진 + 정서 모니터링(emotion_scores/emotion_alerts) (Phase 2) — 테이블만 존재, 엔드포인트·피처플래그 OFF
7. [ ] 비서 엔진 + 출판 파이프라인 + 외부 연계 옵션 파일럿 (Phase 3) — schedule 모듈은 조회·응답만 구현, `publications` 테이블만 존재

> Do 단계 진행(PR #1~19): PII 1·2차 필드 암호화(§7.3), Keycloak JWKS 실 인증·RBAC/IDOR(§7.4), consent·notifications 모듈, social_worker fail-closed, 모바일 온보딩+앱시작게이트, 로컬 Keycloak realm, import-linter, `core/auth.py` 순수화, Compaction Engine·Critic Agent(§2.11 3·4단계), apps/web·apps/admin Keycloak 로그인. 실 인프라 e2e 17/17·13/13·9/9. PDCA Check 2회(`docs/03-check/`).

### 11.3 Session Guide

| Session | Phase | Scope | Turns |
|---------|-------|-------|:-----:|
| Session 1 | Plan + Design | 전체 (본 문서) | 완료 |
| Session 2 | Phase 1+2 | 스키마·컨벤션 확정 | 완료 |
| Session 3 | Do | `--scope module-author-engine` | 40-50 |
| Session 4 | Do | `--scope module-mobile-offline-core` | 40-50 |
| Session 5 | Check + Report | 전체 | 30-40 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.27 | 2026-09-10 | **PDCA Check — 설계문서↔구현 갭 분석 반영.** ① §9.1 Layer Structure·§11.1 File Structure를 실제 모듈러 모놀리스 구조(`services/backend/src/core_service/modules/{name}/{4계층}` + `core/` + `shared/`, `main.py`/`worker.py`)로 교체 — 기존 `services/{engine}/` 6-서비스 트리는 미구현(decisions.md #44, structure.md v1.4는 이미 정정됨). ② §3.1 `interface Chapter`에서 `createdAt` 제거(테이블·ORM·응답·DDL 어디에도 없던 필드, v0.6 L-11에서 추가됐으나 미구현). ③ §8.1 Test Plan phase 열 정정(정서 모니터링 Phase 2·피처플래그 OFF, 출판 Phase 3 — §11.2/decisions #25와 정합). ④ §11.2 Implementation Order 체크박스를 실제 상태로 갱신. ⑤ §11 preamble: import-linter 미도입 상태 명시(모듈 경계·4계층은 준수 중이나 CI 회귀 방지 없음 — 후속). schema.md DDL ↔ 실 DB 21개 테이블은 일치 확인 | NUBiz AX Initiative |
| 0.28 | 2026-09-10 | Do 단계 — 모바일 앱 시작 게이트 구현(§2.9 구현 상태 v0.28). `presentation/AppEntry.kt`가 `device_state.device_id`로 온보딩 스킵 판정, 없으면 온보딩 → `presentation/sync/FirstSyncScreen.kt`(최초 Wi-Fi 동기화, §2.9 흐름의 마지막 단계) → 홈. `installmode/KioskController.kt`로 install_mode="kiosk" 시 lockTask 진입(decisions.md #6). `SyncWorker.doWork()`의 동기화 절차를 `sync/SyncRunner.kt`로 분리(Worker·화면 공유). 가족 초대 화면은 미포함(Device Token은 `POST /invitations` 권한 없음 — 첫 가족 연결 경로 별도 결정 대기). mobile-schema.md v0.8 | NUBiz AX Initiative |
| 0.29 | 2026-09-10 | Do 단계 — import-linter 도입(§11). CTO Enterprise B3 "import-linter로 CI에서 경계 차단" 권고 구현. `services/backend/pyproject.toml [tool.importlinter]` contract 4개(모듈 4계층 layers, domain 프레임워크 의존 금지, shared/·core/의 modules 의존 금지) + `ci.yml` backend job `lint-imports` 스텝. 도입 중 `modules/photo_requests/__init__.py` 누락 발견·수정(정적 도구가 패키지 인식 못 하던 결함, gap-analysis G6). `core/auth.py`→모듈 infrastructure 결합 2건은 예외로 고정(후속 리팩터링) | NUBiz AX Initiative |
| 0.30 | 2026-09-10 | Do 단계 — `core/auth.py` 순수화. import-linter contract ④의 예외였던 auth→모듈 infrastructure 결합 2건 제거. `core/auth.py`는 순수(토큰 검증·인가 규칙·조회 포트 Protocol), 리포지토리 조립 FastAPI 의존성은 `core_service/auth_deps.py`(최상위 조립 모듈)로 이동, 13개 라우터가 `auth_deps`에서 인증 심볼 import. `e2e_keycloak_check.py` cleanup FK 순서 버그도 수정. 실 인프라 e2e 17/17·13/13·9/9 재확인 | NUBiz AX Initiative |
| 0.31 | 2026-09-10 | Do 단계 — 챕터 Compaction Engine(§2.11 4단계) 요약·키워드 부분 구현. `LLMClient.compact_chapter`(vLLM) + `ChapterService.compact_chapter`(stale 판정 `compacted_version != version`) + 업로드 파이프라인 best-effort 호출. `chapters`에 `compaction_summary`/`compaction_keywords`/`compacted_version` 컬럼(마이그레이션 0007). `GET /sync/download`가 `body_text` 원문 대신 요약(없으면 앞 200자)을 내려보냄. 페르소나 JSON 룰셋(§2.10 연동)은 미구현. schema.md v1.12, sync-contract.md §5 | NUBiz AX Initiative |
| 0.32 | 2026-09-10 | Do 단계 — Critic Agent(§2.11 3단계) 구현. `questions` 큐에 생성 경로 신설(이전엔 read-only). `LLMClient.critique_and_generate_questions`(vLLM, Fact/Emotion/Relation/Reflection 4축) + `QuestionService.generate_followups`(큐 범람 방지 8개 상한, 중복·잘못된 type 제거) + 업로드 파이프라인 best-effort 호출. `questions.count_unanswered_by_user`/`create_many` 신규. 실 DB로 삽입·카운트 검증. 유닛테스트 8건 추가(155개). 4축 점수 저장·노출은 미구현 | NUBiz AX Initiative |
| 0.33 | 2026-09-11 | Do 단계 — apps/web `(family)/notification-settings` 화면 신규. `notifications` 모듈(PR #3, `GET/PUT /family-members/{id}/notification-settings`)의 첫 웹 소비자 — 3채널(push/email/sms) × 3항목(챕터갱신/동기화문제/정서알림) 그리드, PUT 전체 교체. `types/notification-setting.ts`(구 `consent-log.ts`의 스테일 `NotificationSetting` 대체), `services/notification-settings.ts`, `features/notification-settings/NotificationSettingsForm.tsx`. §5.1 인벤토리에 구현 상태(✅/스텁/OFF) 표기 + 웹 콘솔 Keycloak 로그인 연동이 선결이라는 공통 미완 명시 | NUBiz AX Initiative |
| 0.34 | 2026-09-11 | Do 단계 — apps/web Keycloak 로그인 연동(decisions #49, 사용자 결정: Auth.js/NextAuth v5). §7.4에 웹 콘솔 로그인 항목 추가, §5.1 인벤토리에서 "Bearer dev 공통 미완" 해소(web은 실 Bearer 동작, admin만 미연동). `silveryarn-web` public client + PKCE, `lib/api/client.ts` server-only + Server Action 경로, Next.js 16 `proxy.ts`. 로컬 실 flow(Keycloak 로그인 → 세션 → 백엔드 조회·PUT → DB) 브라우저 검증 | NUBiz AX Initiative |
| 0.35 | 2026-09-11 | Do 단계 — apps/admin Keycloak 로그인 연동(decisions #49, apps/web과 동일 Auth.js). §5.1·§7.4에 admin도 완료 반영. realm `silveryarn-web` `redirectUris`에 `localhost:3001/*` 추가(`infra/keycloak/import/silveryarn-realm.json`·README). admin은 GET 전용이라 Server Action 없이 `lib/api/client.ts` server-only만. 브라우저 flow 검증(로그인 → `require_roles(admin)` 통과 → 사용자·동기화 목록 조회) | NUBiz AX Initiative |
| 0.39 | 2026-09-11 | Do 단계 — `POST /chapters/{id}/review` 승인 시 Compaction 재확인 안전망(gap-analysis-2026-09-11 G11 후속 #3). 감수는 `body_text`/`version`을 바꾸지 않아(`update_status` `bump_version=False` 기본값) 평소엔 `compact_chapter(force=False)`가 재조회만 하고 끝나지만, 직전 `save_draft` 시점 압축이 vLLM 장애로 실패했던 경우 확정 시점에 한 번 더 시도한다. best-effort — 실패해도 승인 응답은 그대로 200. 실 인프라(vLLM 미기동 상태 포함) 검증: 승인 200 + `status=confirmed` 확인, 예외 시 폴백 로그도 확인 | NUBiz AX Initiative |
| 0.38 | 2026-09-11 | Do 단계 — 모바일 홈 셸(M2, UI/UX 화면설계서) 구현. `presentation/home/HomeScreen.kt`(인사 헤더·마이크 CTA·오늘의 회고 질문 카드·통계 바) + `presentation/AppShell.kt`(하단 탭 4개: 대화/자서전/일정/설정 — `AppEntry.kt`의 `AppState.Home`이 이제 이걸 그린다). 통계는 로컬 DB만 조회(오프라인 완결, §2.1): `autobiography_fts` DISTINCT chapter_id(완성 챕터), `conversations` distinct 날짜로 계산한 연속 대화일수(§3 retention 5일이 상한), `unrecalled_photos` COUNT. mobile-schema.md v0.10 — `device_state.user_name` 신규(인사말용, `POST /devices` 응답엔 이름이 없어 온보딩 값을 별도 저장). ⚠️ "대화" 탭 마이크 세션은 온디바이스 SLM 의도 라우터(workflow-diagrams.md §19)가 아직 스텁이라 말벗돌봄 모드(M4)로 고정 — 라우터 구현 시 `AppShell`의 분기만 교체 | NUBiz AX Initiative |
| 0.37 | 2026-09-11 | Do 단계 — 웹·가족 대시보드 "오늘의 기억 리포트"(WF1) 구현. `(family)/dashboard` 신규 — 오늘 대화 수(신규 `GET /users/{id}/conversation-chunks/count?since=`, PII 복호화 없이 COUNT만)·오늘 새 회고 수·"주요 회고 카드"(§2.11 4단계 Compaction 요약을 `ChapterResponse.compaction_summary/keywords`로 최초 노출). WF1의 "정서 상태"·"정서 추이 차트"는 렌더하지 않고 파이프라인 OFF 사실을 안내(decisions #25) — §9.1 화면 인벤토리 갱신 | NUBiz AX Initiative |
| 0.36 | 2026-09-11 | **PDCA Check #2** (`docs/03-check/gap-analysis-2026-09-11.md`) — 1차 Check 이후 PR #10~19 반영. §11.2 Implementation Order 스테일 정정(item 1: schema.md v1.11→v1.12·마이그레이션 0006→0007; item 5: Compaction Engine "미구현"→구현됨 PR #15, Critic Agent PR #16 추가; preamble: PR #1~19). §11.1 트리 "Alembic 0001~0006"→0007. structure.md 모듈 수(8/10→12)·orphan cleanup "미구현"→구현됨 정정. §4.2 endpoint 표에 없는 구현 헬퍼 6종은 경미(표가 "초안"·버전 로그에 기록)로 후속. schema DDL↔실 DB·4계층·import-linter 정상 확인 | NUBiz AX Initiative |
| 0.1 | 2026-09-05 | Plan/ 폴더 원본 문서 4종 기반 Design 초안 등록 | NUBiz AX Initiative |
| 0.2 | 2026-09-05 | design-validator 검증 반영 — RAG/정서모니터링/출판/온보딩/상태전이/Diff처리/페르소나 절 신설(§2.4~2.10), API 표준화(§4), RBAC·백업정책 추가(§7), 데이터모델 v1.1 동기화(§3), Domain 레이어 위치 정정(§9) | NUBiz AX Initiative |
| 0.3 | 2026-09-06 | 사용자 제안 "Closed-Loop Architecture" 보고서 검토 반영 — §2.11 신설(Opus/WorkManager/Whisper Large-v3/Neo4j/Critic Agent/Compaction Engine 구체화), 컴포넌트 다이어그램·의존성표에 Neo4j 추가, §4.3에 sync/download 응답 예시 추가. 외부 GPT-4o/Claude 제안은 미채택(온프레미스 vLLM 유지, decisions #26) | NUBiz AX Initiative (사용자 제안 반영) |
| 0.4 | 2026-09-06 | 사용자 제안 "저사양 실시간 대화 프로세스" 보고서 반영 — §2.12 신설(8단계 파이프라인, 메모리 예산 목표치), 로컬 RAG를 FTS5 단독(Phase 1 기본, decisions #32)으로 확정해 §2.3/§9.1의 "경량 VectorDB" 표현 정정, mobile-schema.md 신규 연계 | NUBiz AX Initiative (사용자 제안 반영) |
| 0.5 | 2026-09-07 | 2차 design-validator 검증 반영 — ConversationChunk/Device 등 TS 인터페이스에 schema.md v1.3 신규 컬럼 동기화(session_id/turn_id/mode/assistantResponse, slmModelVersion/promptPackVersion), 누락 필드 보강(bodyTextSnapshot/qualityFlag/retryCount/expiresAt), Neo4j를 §9.1 Infrastructure 레이어에 추가, 교차참조 오류 정정(§2.9→workflow-diagrams §7, §2.4→§2.8, §4.2→§4.3), 6개 마이크로서비스 첫 커밋 금지 경고를 §11에 직접 명시, erd.md 링크 추가 | NUBiz AX Initiative |
| 0.6 | 2026-09-07 | 3차 design-validator 검증 반영 — H-3: [sync-contract.md](../sync-contract.md) 신규 작성 및 §4.2/§6.1에서 링크(비동기 업로드 202+job_id, 엔티티별 충돌정책으로 Server-Wins 전면적용 폐기, Presigned URL 사진업로드, 증분 다운로드), 429/413 에러코드 추가. M-8: `GET /devices/{userId}`를 소유자 중첩 규칙에 맞게 `/users/{userId}/devices`로 정정 + 예외 규칙 명시. L-12: questions/schedule-items/consent-logs 엔드포인트 추가. L-5: §2.11의 §2.8 오참조를 workflow-diagrams §7로 정정. L-11: Chapter.createdAt/updatedAt, Photo.uploadedAt, ScheduleItem.nextRemindAt/respondedAt 필드 보강 | NUBiz AX Initiative |
| 0.7 | 2026-09-08 | Do 단계 — apps/admin 스캐폴딩 중 실제 구현(core_service)이 이미 앞서 있던 필드 2건을 TS 인터페이스에 보강(SoR 원칙 2: 코드 존재 시 코드 우선). Device.aiTops/lastSyncAt, SyncSession.startedAt/finishedAt 추가 | NUBiz AX Initiative |
| 0.8 | 2026-09-08 | apps/admin 동기화 모니터링용 `GET /sync/sessions?deviceId=`(§4.3)와 전체 사용자 목록용 `GET /users?page=&pageSize=`(§4.3, F-3 예외) 신규 엔드포인트를 API 표에 반영 — 둘 다 Admin 전용 조회 엔드포인트로, 기존 Device Token 인증 엔드포인트와 인가모델을 분리했다 | NUBiz AX Initiative |
| 0.9 | 2026-09-08 | apps/admin `(admin)/users` 사용자 목록 화면(신규) — `GET /users`를 실제로 쓰는 첫 화면. User.createdAt/updatedAt이 실제 UserResponse에는 있었지만 §3.1 TS 인터페이스에 누락돼 있던 걸 발견·보강(SoR 원칙 2, Device/SyncSession과 동일 패턴) | NUBiz AX Initiative |
| 0.10 | 2026-09-08 | `GET /sync/sessions`를 페이지네이션+"전체 기기 통합 모니터링"으로 확장 — `deviceId`가 선택이 됐고(생략 시 전체 기기), `status` 필터·페이지네이션 추가(§4.2). `(admin)/sync-monitor`가 같은 라우트로 기기별/전체 두 모드를 겸함. `idx_sync_started_at` 인덱스 신규(schema.md v1.5) — 기기 무관 전역 정렬은 기존 `idx_sync_device`(device_id 선두 컬럼)로 못 타기 때문 | NUBiz AX Initiative |
| 0.11 | 2026-09-08 | `GET /sync/sessions` 응답에 `deviceDisplayId` 추가(§4.2) — devices 모듈의 신규 `DeviceService.get_display_ids()`(IN 쿼리 일괄 조회)를 라우터에서 조합, sync 모듈이 devices 테이블을 직접 조인하지 않는 원칙(structure.md §2)은 유지. SyncSession 엔티티(§3.1) 자체 컬럼이 아니라 이 응답에서만 붙는 필드임을 명시 | NUBiz AX Initiative |
| 0.12 | 2026-09-08 | `GET /users`에 `name` 이름 검색 파라미터 추가(§4.2, ILIKE 부분일치) — apps/admin `(admin)/users` 화면에 검색창 신설. care 모듈의 conversation_chunks ILIKE 검색과 달리 "실제 하이브리드 서치로 교체 예정" TODO 없음(단순 이름 문자열 매칭이라 ILIKE가 최종 구현) | NUBiz AX Initiative |
| 0.13 | 2026-09-08 | `photo_requests` 모듈 완성 — §4.2에 `GET /users/{userId}/photo-requests`·`POST /photo-requests/{id}/dismiss` 신규(스캐폴딩 시점 추가, invitations 모듈과 동일 사유). 충족(fulfilled)은 별도 엔드포인트 없이 `POST /photos/{id}/complete`가 devices/deps.py 패턴으로 photo_requests 모듈을 호출해 자동 처리 — schema.md §3.7 `fulfilled_at`("사진 업로드로 충족된 시각")이 이미 전제하던 흐름 | NUBiz AX Initiative |
| 0.16 | 2026-09-08 | apps/web `(family)/photo-requests` 사진 요청 화면 신규 — photo_requests API를 소비하는 첫 화면(생성/조회/닫기). §3.1 `PhotoRequest` 인터페이스에 `createdAt`/`fulfilledAt` 보강(실 응답엔 있었으나 누락) | NUBiz AX Initiative |
| 0.15 | 2026-09-08 | apps/web `(user)/photos` 사진 갤러리 화면 신규 — §5.1 화면 인벤토리의 "사진·타임라인 갤러리" 최초 구현, sync-contract.md §4 Presigned URL 흐름을 처음 소비하는 웹 화면. §3.1 `Photo` 인터페이스에 `status`(schema.md v1.6엔 있었으나 누락)·`viewUrl`(신규, MinIO presigned GET URL — storageRef는 내부 키라 브라우저가 못 열어서 추가) 보강. `GET /users/{userId}/photos`에 `view_url` 필드 추가(`PhotoService.get_view_url`, 실 MinIO로 검증) | NUBiz AX Initiative |
| 0.14 | 2026-09-08 | `GET /sync/download` 실제 구현(§4.2, sync-contract.md v0.3) — `deviceId` 필수 파라미터 신규(원문엔 없었으나 Device Token 스텁이라 호출 주체 식별 수단이 필요했음). author 모듈에 `questions` 도메인/리포지토리/서비스 신규(schema.md §3.9 테이블은 있었으나 코드가 없었던 갭, photo_requests와 동일 패턴), schedule 모듈에 `deps.py` 신규. chapter_updates의 summary/keywords는 §2.11 Compaction Engine 미구현으로 body_text 원문/빈 배열 대체. §4.3 예시에 `priority_questions.linked_chapter_id` 보강(questions 엔티티엔 있는 실 데이터인데 원래 예시에 빠져 있었음) — 상세는 sync-contract.md §5 | NUBiz AX Initiative |
| 0.17 | 2026-09-09 | Do 단계 — §7.3 신설(PII 필드 암호화). CTO 보안 검토 B4 "Do 단계 이연 불가" 항목 착수: `chapters.body_text`·`chapter_revisions.body_text_snapshot`·`conversation_chunks.{transcript_on_device, transcript_server, assistant_response}` 5개 컬럼에 애플리케이션 레벨 필드 암호화 + 사용자별 DEK 적용([decisions.md #45](../../01-plan/decisions/silveryarn-platform.decisions.md), schema.md v1.7). `name`/`contact`/`birth_date`는 2차 라운드. §7.2 백업 스냅샷 암호화 경고 추가 | NUBiz AX Initiative |
| 0.19 | 2026-09-09 | Do 단계 — 실 인증. §7.4 신설(Keycloak JWKS RS256 검증, Device Token=`device_credentials` SHA-256, `authorize_user_access` RBAC+IDOR, `access_logs` 미들웨어). `core/auth.py` 스텁 교체. `POST /devices` 응답에 `device_token` 1회 발급. `POST /chapters/{id}/review`의 `reviewer_id`를 토큰 파생으로 전환. schema.md v1.8(keycloak_sub·device_credentials·access_logs), erd.md §11(3종 반영), decisions.md #47 | NUBiz AX Initiative |
| 0.26 | 2026-09-09 | Do 단계 — `infra/docker-compose.yml`에 Keycloak(로컬, port 9678) + `infra/keycloak/import/silveryarn-realm.json`(--import-realm 자동). §7.4에 실 인프라 e2e 결과 추가: `e2e_keycloak_check.py` 9/9(JWKS·RBAC·social_worker fail-closed·2FA amr), `e2e_pii_auth_check.py` 17/17, `e2e_http_smoke.py` 13/13. 버그 수정: 무인증 요청 401(500 아님) | NUBiz AX Initiative |
| 0.25 | 2026-09-09 | Do 단계 — 모바일 온보딩 화면 흐름 구현(§2.9 구현 상태). 상태 호이스팅(sealed `OnboardingStep` + `when`, **Navigation/ViewModel 프레임워크 미도입 확정** — 선형 흐름엔 과함, 화면 늘면 재검토). `OnboardingScreen`(이름→동의→완료) + `OnboardingCoordinator`(createUser→POST /devices→recordConsent 3연쇄). mobile-schema.md v0.7 | NUBiz AX Initiative |
| 0.24 | 2026-09-09 | Do 단계 — social_worker fail-closed. `READ_ELDER_DATA_ROLES`에서 social_worker 제외(family/caregiver/admin만). RBAC §7.1 "동의 시"를 표현할 consent 유형이 없고 제3자제공 법무 판단 대기라 안전 측으로 조회 자체를 막음. 전용 유형 확정 시 재포함. decisions.md 0.16 | NUBiz AX Initiative |
| 0.23 | 2026-09-09 | Do 단계 — PII 2차(decisions.md #45 2차, schema.md v1.11, 마이그레이션 0006). `family_members.contact`·`invitations.contact` 암호문 + `contact_bidx`(HMAC 동등검색), `users.birth_date` 앱 레이어 암호화(DATE→VARCHAR), **`name` 평문 유지 확정**. §7.3 표를 1/2/3차로 재구성. `invitations`가 `contact_bidx`로 중복 초대 차단. `core/crypto.py`에 `blind_index` 추가, user/family_member/invitation repo에 `PiiFieldEncryptor` 주입 | NUBiz AX Initiative |
| 0.22 | 2026-09-09 | Do 단계 — `notifications` 모듈 신설. `GET/PUT /family-members/{id}/notification-settings`(§4.2) — WF5 알림 설정. PUT은 이 구성원 설정 전체 교체(delete→insert). 인가는 `authorize_own_family_member`(신규 — "본인 것만", RBAC §7.1) + 2FA. CTO B1 반영: `receives_emotion_alerts` 기본값 opt-in(false), `(family_member_id, channel)` UNIQUE. schema.md v1.10, 마이그레이션 0005 | NUBiz AX Initiative |
| 0.21 | 2026-09-09 | Do 단계 — 인가(RBAC/IDOR) 확대. §7.4에 family-members·invitations·photo-requests 적용 추가. `POST /invitations/{token}/accept`가 `require_verified_subject`(신규 — 토큰만 검증)로 수락자 `sub`를 `family_members.keycloak_sub`에 연결(없으면 수락 후 로그인 불가였던 갭). `create_family_member`에 `keycloak_sub` 파라미터. social_worker "동의 시 조회"는 전용 consent 유형 결정 필요로 미도입 | NUBiz AX Initiative |
| 0.20 | 2026-09-09 | Do 단계 — 동기화 계약 잔여분. ① 업로드 멱등성 3계층(arq `_job_id`·파이프라인 사전 확인·부분 유니크 인덱스, sync-contract.md §2.3, schema.md v1.9, 마이그레이션 0004). ② `GET /users/{userId}/questions` 실제 구현(§4.2 — `questions` 모듈에 라우터·`list_by_user` 추가, `answered` 필터). ③ `schedule_items` Device-Wins 필드 병합이 `/schedule-items/{id}/respond` 엔드포인트로 이미 실현됨을 sync-contract.md §3에 명시(배치 병합 코드 불필요) | NUBiz AX Initiative |
| 0.18 | 2026-09-09 | Do 단계 — `consent` 모듈 신설. §4.2에 `POST /users/{userId}/consent-logs`(§2.9 온보딩이 전제하던 '동의 기록' 경로가 표에 없던 갭)·`GET .../consent-state` 추가. §3.1 `ConsentLog`에 `actor`(self/proxy, `granted_by` 파생 — CTO B2)·`grantedAt`(실 응답엔 있었으나 누락) 보강. §2.9에 구현 상태·B2 미도입 사유 명시. 모바일 `OnboardingApi.kt`(createUser→recordConsent 계약) 추가, 화면 흐름은 후속 | NUBiz AX Initiative |
