---
template: design
version: 1.3
---

# silveryarn-platform Design Document

> **Summary**: 온디바이스 오프라인 우선 + 온프레미스 서버 하이브리드 아키텍처 기술 설계
>
> **Project**: 은빛실타래 (SilverYarn)
> **Version**: 0.13 (photo_requests 모듈 완성 반영)
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

**4단계 — 온디바이스 맞춤형 경량화 패키징 (Compaction Engine)**
- 서버 확정 챕터 요약·핵심 키워드를 온디바이스 SQLite FTS5 테이블용 차분 데이터로 컴파일 (§2.4 "경량화 스냅샷 생성"의 구체 산출물)
- 다음 대화용 "단기 압축 기억(Short-term Compressed Persona)" JSON 룰셋 생성 — §2.10 페르소나 정의와 연동

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
  createdAt: string;            // v0.6 신규 — 3차 검증 L-11
  updatedAt: string;            // v0.6 신규 — 3차 검증 L-11
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
}

interface PhotoRequest {       // v1.1 신규
  id: string;
  userId: string;
  requestedBy?: string;
  message?: string;
  status: "pending" | "fulfilled" | "dismissed";
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
  granted: boolean;
  grantedBy?: string;
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
| GET | /api/v1/sync/download?since={syncVersion} | 최신 자서전·RAG 스냅샷·사진·질문목록 다운로드 — `since` 지정 시 증분만 반환 ([sync-contract.md §5](../sync-contract.md#5-증분-다운로드-be-b4)) | Device Token |
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
| PUT | /api/v1/family-members/{id}/notification-settings | 알림 수신 채널·항목 설정 | 2FA + Role(family) |
| POST | /api/v1/invitations | 가족 구성원 초대 | 2FA + Role(family) |
| POST | /api/v1/users/{userId}/publications | 인쇄/출판 요청 | 2FA + Role |
| GET | /api/v1/users/{userId}/devices | 기기 사양·설치모드 조회 (관리자, 조회 전용) — *(v0.6: `/devices/{userId}` → 소유자 중첩 규칙에 맞게 정정, M-8)* | Admin |
| GET | /api/v1/users?page={page}&pageSize={pageSize}&name={name} | 전체 사용자 목록 조회, 페이지네이션(신규 0.8) + 이름 부분일치 검색(신규 0.12) — F-3 예외(사전에 소유자를 특정할 수 없는 전역 조회) | Admin |
| GET | /api/v1/users/{userId}/questions | 회고 질문 큐 조회 (신규, L-12) | 2FA + Role |
| GET | /api/v1/users/{userId}/schedule-items | 일정/복약 목록 조회 (신규, L-12) | 2FA + Role |
| GET | /api/v1/users/{userId}/consent-logs | 동의 이력 조회 (신규, L-12) | 2FA + Role |

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
      { "question_id": "q_...-uuid", "text": "인천 공장 계실 때 첫 월급 타서 사모님께 어떤 선물을 하셨는지 기억나세요?", "type": "follow_up" }
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

| 영역 | 화면 |
|---|---|
| 모바일앱(당사자) | 온보딩·동의, 홈·음성대화, 자서전 작가모드 인터뷰, 말벗돌봄 대화, 비서모드 일정·복약, 설정·동기화 상태, 사진 추가하기 |
| 웹·자서전 사용자 | 로그인·대시보드, 자서전 뷰어, 사진·타임라인 갤러리, ~~구독·결제 관리~~(스코프 아웃, decisions.md #18), 계정 설정 |
| 웹·가족 | 가족 대시보드(오늘의 기억 리포트), 원고 감수·대조편집, 사진 업로드·타임라인 배치, 정서 모니터링 상세, 알림·가족구성원 설정 |
| 웹·관리자 | 관리자 대시보드, 사용자 관리, Wi-Fi 동기화 모니터링, 정서 알림 이력 관리, 시스템 설정·리소스 모니터링, 기기 관리(설치모드/사양) |

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

- [ ] DB 암호화(AES-256) 및 전송구간 암호화(TLS 1.3) — 온디바이스 로컬 캐시도 동일 수준
- [ ] 웹 콘솔 2FA, 역할별 차등 열람 권한(가족/복지사/관리자) — §7.1 RBAC 매트릭스 참조
- [ ] 외부 연계(3.4절) 시 PII 마스킹 전처리 + 동의 로그 필수, 미동의 시 전량 온프레미스 경로
- [ ] Wi-Fi 동기화는 등록된 신뢰 네트워크에서만 수행 — 등록 정보는 온디바이스 로컬 전용 저장([decisions.md #22](../../01-plan/decisions/silveryarn-platform.decisions.md))
- [ ] Device Owner Mode(COSU) 채택 확정([decisions.md #6](../../01-plan/decisions/silveryarn-platform.decisions.md)) — 단말 탈취·우회 방지 상세 구현은 Do 단계에서 검토
- [ ] **설치모드 판별 임계값(확정 수치)**: `ram_gb < 6 OR android_version <= '11'` → kiosk ([decisions.md #5](../../01-plan/decisions/silveryarn-platform.decisions.md), [schema.md §3.3](../../01-plan/schema.md)) — design-validator C-1 반영, 구현 기준 문서인 본 절에 수치 직접 명기

### 7.1 RBAC 권한 매트릭스 (신규 v0.2, design-validator E-8)

> 기획서 6장 "역할별 차등 권한" 요구를 구체화. 세부 조정은 Do 단계.

| 리소스 | family | caregiver | social_worker | admin |
|---|:-:|:-:|:-:|:-:|
| 챕터 조회 | ✅ | ✅ | ✅(동의 시) | ✅ |
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
| 정서 모니터링 | emotion_scores 일별 기록, 임계치 초과 시 emotion_alerts 생성·알림 발송(§2.5) | E2E 시나리오 | Do |
| 출판 파이프라인 | 챕터 전체 confirmed → publications 요청 → PDF/ePub 생성(§2.6) | E2E 시나리오 | Do |

---

## 9. Clean Architecture

### 9.1 Layer Structure (Enterprise, On-Premise 변형)

| Layer | Responsibility | Location |
|-------|---------------|----------|
| **모바일 Presentation** | 음성 UI, 대화 화면, 사진 업로드 UI | `apps/mobile/` |
| **모바일 On-Device AI** | VAD·STT·SLM·TTS, 로컬 라우터 | `apps/mobile/ondevice/` |
| **모바일 Infrastructure** | 로컬 SQLite(FTS5, Phase 1 기본 — [mobile-schema.md](../../01-plan/mobile-schema.md)), 경량 VectorDB(Phase 2+, 고사양 단말 한정), 동기화 클라이언트 | `apps/mobile/local/` |
| **서버 Presentation** | API Gateway, 웹 콘솔(`apps/web`, `apps/admin`) | `services/gateway/`, `apps/web/`, `apps/admin/` |
| **서버 Application** | author-engine, care-engine, schedule-engine 유스케이스 | `services/{engine}/application/` |
| **서버 Domain** | 서비스별 Entity·비즈니스 규칙(챕터 귀속, 사진 인라인 규칙) | `services/{engine}/domain/` — *v0.2: `services/shared/domain/`(단일 공유)에서 structure.md와 일치하도록 서비스별 분산으로 정정(design-validator F-2). `services/shared/`는 순수 공통 유틸·마이그레이션만 담당* |
| **서버 Infrastructure** | Qdrant/Neo4j/PostgreSQL/MinIO 연동, vLLM 클라이언트 | `services/{engine}/infrastructure/` |

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

> ⚠️ **CTO팀 아키텍처 리뷰 권고(Enterprise B3)**: 아래 6개 서비스 구조를 첫 스캐폴딩 커밋에서 그대로 6개 독립 배포 단위로 찍지 말 것. Phase 1은 **모듈러 모놀리스 2프로세스(api / worker)**로 시작하고, 폴더 경계만 아래 구조로 유지하며 import-linter로 엔진 간 직접 참조를 CI에서 차단하는 방식을 권장한다. 실제 서비스 분리는 GPU 스케일 독립이 필요해지는 시점(rag-core 등)에 재검토([cto-review](../cto-review-2026-09-05.md#1-enterprise-architect--아키텍처-전략-심사) B3 참조).

### 11.1 File Structure (제안)

```
silveryarn/
├── apps/
│   ├── mobile/            # 온디바이스 앱 (설치모드 자동분기 포함)
│   ├── web/                # 자서전 사용자·가족 웹 콘솔
│   └── admin/               # 관리자 콘솔
├── services/
│   ├── gateway/             # API Gateway/오케스트레이터 (Keycloak 연동)
│   ├── author-engine/
│   ├── care-engine/
│   ├── schedule-engine/
│   ├── sync-gateway/        # Wi-Fi 배치 동기화 처리
│   ├── rag-core/            # LLM·임베딩·Vector DB 오케스트레이션
│   └── shared/               # 공통 유틸·Alembic 마이그레이션만 (도메인 로직 없음 — §9.1)
├── packages/
│   └── py-common/            # 서비스 간 공유 Python 패키지
├── infra/                   # 온프레미스 K8s/베어메탈 GPU 클러스터 (AWS 템플릿 미적용)
├── docs/                     # PDCA 문서
└── Plan/                     # 원본 기획 산출물 (보존)
```

### 11.2 Implementation Order

1. [x] Phase 1 스키마 확정 (`/phase-1-schema`) — v1.3, 17개 엔티티
2. [x] Phase 2 컨벤션 확정 (`/phase-2-convention`)
3. [ ] 온디바이스 오프라인 코어(STT/SLM/TTS) + 로컬 캐시
4. [ ] Wi-Fi 배치 동기화 기본 흐름 (업/다운로드, 재시도, 체크섬, Diff 멱등성)
5. [ ] 자서전 작가 엔진 + 웹 콘솔 감수 흐름 (Phase 1 MVP)
6. [ ] 말벗돌봄 엔진 + 정서 모니터링(emotion_scores/emotion_alerts) (Phase 2)
7. [ ] 비서 엔진 + 출판 파이프라인 + 외부 연계 옵션 파일럿 (Phase 3)

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
