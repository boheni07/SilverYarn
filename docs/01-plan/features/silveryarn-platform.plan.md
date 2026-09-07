---
template: plan
version: 1.3
---

# silveryarn-platform Planning Document

> **Summary**: 어르신 자서전 제작과 AI 말벗돌봄을 온디바이스(오프라인 우선)-온프레미스 서버 하이브리드 구조로 통합 제공하는 플랫폼
>
> **Project**: 은빛실타래 (SilverYarn)
> **Version**: 0.4 (3차 design-validator 검증 반영)
> **Author**: NUBiz AX(AI Transformation) Initiative
> **Date**: 2026-09-07
> **Status**: Draft

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | 고령화로 어르신의 삶의 기록이 소실되고, 독거·정서적 고립으로 인한 돌봄 공백이 커지고 있음. 재활용·저사양 단말 사용자와 인터넷 상시 연결이 어려운 시니어 생활 환경도 고려 필요 |
| **Solution** | 스마트폰 온디바이스 STT/SLM/TTS로 평소 대화(자서전 구술·말벗돌봄·비서)를 오프라인에서 완결시키고, 등록 Wi-Fi(자택 등) 접속 시에만 온프레미스 서버(LLM·RAG·VectorDB)와 배치 동기화하여 자서전·대화 품질을 정교화하는 하이브리드 아키텍처 |
| **Function/UX Effect** | 인터넷 불안정 환경에서도 끊김 없는 대화, 사진 기반 자동 회고 트리거로 자연스러운 자서전 콘텐츠 축적, 저사양 재활용 단말은 키오스크 모드로 자동 설치되어 혼란 없는 전용 사용 경험 제공 |
| **Core Value** | 자서전 제작(입구) → 말벗돌봄·비서(체류)로 이어지는 3단계 라이프사이클을 단일 플랫폼에서 통합 제공, 본인의 실제 인생 서사에 기반한 초개인화 대화로 범용 챗봇 대비 높은 정서적 몰입도 |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | 어르신 삶의 기록 소실 방지 + 독거·고립으로 인한 돌봄 공백 해소, 저사양/재활용 단말 및 상시 인터넷 미보장 환경에서도 동작해야 함 |
| **WHO** | 1차: 구술 주체인 어르신 본인 · 2차: 감수하는 가족, 요양보호사·복지사 · 잠재: 복지관·요양기관·지자체(B2G/B2B, 검증 필요) |
| **RISK** | 가족사·건강 등 초민감 개인정보 처리 리스크 — 온프레미스 원칙(Zero External Data Egress) 위반 시 파급력 큼 (8.2절) |
| **SUCCESS** | Phase 1 MVP에서 오프라인 온디바이스 대화 + Wi-Fi 배치 동기화 기본 흐름이 끊김 없이 동작하고, 자서전 챕터가 실제 구술 내용을 정확히 반영 |
| **SCOPE** | Phase 1(자서전 작가+오프라인 코어) → Phase 2(말벗돌봄 확장) → Phase 3(비서+외부연계 옵션) |

---

## 1. Overview

### 1.1 Purpose

스마트폰 온디바이스 음성 인터페이스(VAD·STT·SLM·TTS)와 중앙 온프레미스 서버 기반 생성형 AI 파이프라인(LLM·RAG·VectorDB)을 연계하여, 어르신의 구술 회고를 오프라인 상태에서도 실시간으로 수집·응답하고, Wi-Fi 접속 시 서버의 고성능 엔진으로 자서전과 대화 내용을 최신화·정교화한 뒤 다시 스마트폰으로 동기화한다.

### 1.2 Background

고령화 심화로 어르신 삶의 기록이 보존되지 못한 채 소실되는 경우가 많고, 독거·정서적 고립으로 인한 돌봄 공백 문제가 커지고 있다. 동시에 재활용 스마트폰 등 저비용 단말을 활용한 시니어 접근성 개선 요구가 높으며, 시니어 생활 환경상 상시 인터넷 연결을 기대하기 어려워 오프라인 우선 구조가 필요하다.

### 1.3 Related Documents

- 원본 기획서: [`Plan/어르신_자서전_말벗돌봄_기획서.md`](../../../Plan/어르신_자서전_말벗돌봄_기획서.md) (v0.5, 부록A 설치모드 판별 기준 포함)
- 프로세스 흐름도: [`Plan/자서전_말벗돌봄_프로세스_흐름도.md`](../../../Plan/자서전_말벗돌봄_프로세스_흐름도.md) (Mermaid 20+ 다이어그램)
- BI 가이드: [`Plan/은빛실타래_BI가이드_v2.html`](../../../Plan/은빛실타래_BI가이드_v2.html)
- UI/UX 화면설계서: [`Plan/은빛실타래_UIUX_화면설계서.html`](../../../Plan/은빛실타래_UIUX_화면설계서.html) (v1.2, 모바일 7화면 + 웹 20+화면)
- Design: [silveryarn-platform.design.md](../../02-design/features/silveryarn-platform.design.md)
- 의사결정 로그: [silveryarn-platform.decisions.md](../decisions/silveryarn-platform.decisions.md) (기획서 9장 항목별 확정/보류 현황)

---

## 2. Scope

### 2.1 In Scope

- [ ] 온디바이스 오프라인 대화 엔진 (VAD·STT·SLM·TTS) — 자서전 작가/말벗돌봄/비서 3대 모드
- [ ] Wi-Fi 배치 동기화 (등록 Wi-Fi 감지 시 자동 업/다운로드, 재시도·체크섬 무결성 검증)
- [ ] 온프레미스 서버 AI 파이프라인 (고정밀 STT 재전사, RAG/VectorDB, LLM 챕터 최신화)
- [ ] 사진 기반 자동 회고 트리거 및 챕터 인라인 편입 파이프라인
- [ ] 설치모드 자동 분기 (키오스크/일반 앱, RAM·OS 버전 기준)
- [ ] 웹 콘솔 (가족 감수·편집, 자서전 뷰어, 관리자 대시보드) — UI/UX 화면설계서 기준
- [ ] 정서 모니터링 및 가족·복지사 알림 연동 — **일별 정서기록(emotion_scores)/알림(emotion_alerts) write 경로는 Phase 1 피처플래그 OFF**(스키마만 존재), 법무 검토(decisions.md #12) 완료 후 Phase 2에서 활성화([decisions.md #25](../decisions/silveryarn-platform.decisions.md))
- [ ] 인쇄용 PDF(CMYK 300DPI)/ePub 자동 조판

### 2.2 Out of Scope (이번 단계)

- 외부 클라우드 AI 연계(고품질 감성 TTS, 범용 보조 LLM) — Phase 1~2는 온프레미스 TTS만 사용, 외부 연계는 Phase 3 검토 대상으로 확정 보류 ([decisions.md #3](../decisions/silveryarn-platform.decisions.md))
- '기억의 서재' 프로젝트와의 통합/중복 검토 — 완전히 별개 프로젝트로 최종 확정, 재점검 불필요 ([decisions.md #4](../decisions/silveryarn-platform.decisions.md))
- **구독·결제 도메인** — PG사·요금제가 경영/법무 결정 사항으로 남아있어 엔티티·API·화면 설계 모두 이번 단계 스코프에서 제외 ([decisions.md #18](../decisions/silveryarn-platform.decisions.md)). UI/UX 화면설계서의 "구독·결제 관리" 화면(WU4)은 결정 이후 별도 설계

> B2C/B2G는 병행 추진으로 확정되었으나([decisions.md #1](../decisions/silveryarn-platform.decisions.md)), 채널별 온보딩·과금 방식은 이번 단계(§2.1 In Scope) 이후 별도 설계한다.

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 온디바이스에서 인터넷 연결 없이 3대 모드(작가/말벗돌봄/비서) 대화가 완결되어야 함 | High | Pending |
| FR-02 | 등록된 Wi-Fi 접속 시 자동으로 배치 동기화(업로드/다운로드)가 수행되어야 함 | High | Pending |
| FR-03 | 신규 사진 업로드 시 미회고 큐에 등록되고 다음 대화 세션에서 우선 제시되어야 함 | High | Pending |
| FR-04 | 사진 기반 회고 결과는 해당 시기 챕터 본문에 자동 인라인 삽입되어야 함 | High | Pending |
| FR-05 | 앱 설치 시점에 RAM·OS 버전을 자동 체크하여 키오스크/일반 모드로 분기 설치되어야 함 | High | Pending |
| FR-06 | 가족은 웹 콘솔에서 AI 챕터 초안을 대조 편집·승인/반려할 수 있어야 함 | High | Pending |
| FR-07 | 발화 톤·부정어 빈도 기반 정서 점수가 임계치 초과 시 가족·복지사에게 알림이 발송되어야 함 | Medium | **On Hold — Phase 1 피처플래그 OFF, decisions.md #25** |
| FR-08 | 일정·복약 발화는 엔티티로 파싱되어 로컬 DB에 등록되고 지정 시각에 능동형 음성 브리핑되어야 함 | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Offline Availability | 인터넷 미연결 상태에서 3대 모드 기본 응답 100% 가능 | 오프라인 모드 QA 시나리오 |
| Data Sovereignty | PII 포함 데이터 100% 온프레미스 처리·저장 (Zero External Data Egress) | 보안 감사, 네트워크 egress 로그 점검 |
| Security | AES-256(저장) / TLS 1.3(전송) 암호화, 2FA(웹 콘솔) | 보안 감사 |
| Sync Resilience | 동기화 실패 시 지수 백오프 재시도 + 체크섬 검증 | 5.6절 흐름 기반 장애 주입 테스트 |
| Device Compatibility | RAM 6GB 미만 또는 Android 11 이하 → 키오스크 모드 (확정 — [decisions.md #5](../decisions/silveryarn-platform.decisions.md)) | 실기기 벤치마크로 미세조정 |

---

## 4. Success Criteria

### 4.1 Definition of Done (Phase 1 MVP 기준)

- [ ] 온디바이스 STT/SLM/TTS 오프라인 대화 흐름 동작
- [ ] 로컬 캐시(최근 5일 대화·자서전 스냅샷) 및 Wi-Fi 배치 동기화 기본 흐름 검증
- [ ] 설치모드 자동 분기(키오스크/일반) 동작
- [ ] 자서전 작가 모드 질문 생성·꼬리질문·챕터 자동 귀속 동작

### 4.2 Quality Criteria

- [ ] 9장 미결 의사결정 항목 중 Phase 1 착수에 필요한 항목(설치모드 임계값, 동기화 트리거 정책) 확정
- [ ] 보안 원칙(3.1절 4원칙) 준수 여부 보안팀 검토 통과

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 민감정보 처리 리스크 (가족사·건강 등) | High | Medium | 하이브리드 온프레미스 원칙(3.1) 준수, 정기 보안 감사 |
| 온디바이스 SLM 성능 한계 (저사양 재활용 단말) | Medium | High | 온디바이스/서버 역할 분담, 모델 경량화 튜닝, 부록A 벤치마크 검증 |
| 오프라인 캐시 정합성 리스크 (장기 미접속) | Medium | Medium | 캐시 용량 관리 정책, 동기화 실패 재시도 로직(5.6절) |
| 정서 모니터링 오탐 리스크 | Medium | Medium | 임계치·검증 프로세스 별도 설계, 법적/윤리적 알림 기준 수립 필요 |
| 설치모드 판별 임계값이 실기기 특성과 어긋날 가능성 | Low | Medium | 부록A 검토안 기반 임계값 확정 완료([decisions.md #5](../decisions/silveryarn-platform.decisions.md)) — 실기기 벤치마크로 미세조정만 남음 |

---

## 6. Impact Analysis

> 신규 프로젝트(그린필드)이므로 기존 리소스에 대한 영향은 없음. '기억의 서재' 프로젝트와는 완전히 별개로 최종 확정되어([decisions.md #4](../decisions/silveryarn-platform.decisions.md)) 재점검이 필요하지 않다 — design-validator 검증(A-2)에서 §2.2와의 자기모순이 지적되어 본 절을 정정함.

### 6.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|--------------------|
| N/A | - | 신규 프로젝트 — 변경 대상 기존 리소스 없음 |

### 6.2 Verification

- [x] 그린필드 프로젝트로 기존 시스템 영향 없음 확인

---

## 7. Architecture Considerations

### 7.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites, portfolios | ☐ |
| **Dynamic** | Feature-based, BaaS integration | Web apps with backend, SaaS MVP | ☐ |
| **Enterprise** | Strict layer separation, DI, microservices, 온디바이스+온프레미스 하이브리드 | 고복잡도 아키텍처, 온프레미스 데이터 주권 요구 시스템 | ☑ |

> 선정 근거: 온디바이스 AI(모바일 네이티브) + 온프레미스 GPU 서버(vLLM/A100) + 다중 엔진(작가/말벗돌봄/비서) + 엄격한 데이터 주권 요구(Zero External Data Egress)가 결합된 구조로 Dynamic 레벨(BaaS 중심)로는 표현이 어려움.

### 7.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 모바일 아키텍처 | Native(Kotlin/Swift) / React Native / Flutter | **Android 네이티브(Kotlin)** | Device Owner API는 Android 전용, 부록A 대상 기기가 전부 Android — [decisions.md #7](../decisions/silveryarn-platform.decisions.md) |
| 키오스크 구현 방식 | Device Owner Mode / Screen Pinning | **Device Owner Mode(COSU)** | Screen Pinning은 사용자가 자체 해제 가능해 잠금 요구 미충족 — [decisions.md #6](../decisions/silveryarn-platform.decisions.md) |
| 온디바이스 SLM | Kanana-2, Qwen2.5-0.5B 등 경량 모델 후보 | **미정** (벤치마크 후보 2종) | '기억의 서재'와는 완전 별개 프로젝트로 확정([decisions.md #4](../decisions/silveryarn-platform.decisions.md)), 최종선정은 실기기 벤치마크 필요([decisions.md #27](../decisions/silveryarn-platform.decisions.md)) |
| 챕터 윤문/Gap분석 LLM | 온프레미스 vLLM vs 외부 GPT-4o/Claude | **온프레미스 vLLM 확정** | 외부 LLM은 Zero External Data Egress 원칙 위반으로 미채택 — [decisions.md #26](../decisions/silveryarn-platform.decisions.md) |
| 백엔드 | 온프레미스 자체 호스팅 (FastAPI 등 Python 계열 권장) | **Python 3.11+/FastAPI 확정** | Zero External Data Egress 원칙(3.1) 준수, CONVENTIONS.md와 정합 — [decisions.md #15](../decisions/silveryarn-platform.decisions.md) |
| 인증(SSO) | Keycloak / 자체 구현 | **Keycloak SSO 확정** | 원본 프로세스흐름도 §4.1이 이미 전제 — [decisions.md #17](../decisions/silveryarn-platform.decisions.md) |
| LLM 추론 | 자체 호스팅 vLLM · A100 서버 | 확정 (기획서 3.3) | 온프레미스 원칙 |
| Vector DB | Qdrant self-hosted | 확정 (기획서 3.3, 5.2) | 하이브리드 서치(BM25+Dense) 자체 호스팅 — Milvus 대안 검토 후 미채택([decisions.md #28](../decisions/silveryarn-platform.decisions.md)) |
| 지식 그래프 | Neo4j self-hosted | 확정 (신규) | 인물·사건·감정 엔티티 관계·타임라인 추적, Qdrant와 상호보완 — [decisions.md #29](../decisions/silveryarn-platform.decisions.md) |
| RDB | PostgreSQL | 확정 (기획서 3.3) | 사용자·일정·복약·원고 이력 |
| Object Storage | 자체 MinIO | 확정 (기획서 3.3) | 원본 음성·완성 PDF/ePub |
| 인프라 호스팅 | AWS/Cloud vs On-Premise Bare-metal/K8s | **On-Premise** | 데이터 주권 원칙상 AWS 등 퍼블릭 클라우드가 아닌 자체 GPU 서버 기반 — bkit Enterprise 기본 템플릿(AWS EKS/RDS)과 다름에 유의 |
| 웹 콘솔 프론트엔드 | Next.js / React | **Next.js(App Router)+TypeScript+Tailwind** | Phase 2 확정 — [CONVENTIONS.md §0.1](../../../CONVENTIONS.md) |

### 7.3 Clean Architecture Approach

```
Selected Level: Enterprise (On-Premise 변형)

┌───────────────────────────────────────────────────────────┐
│ 모바일(온디바이스): presentation(UI) / ondevice(VAD·STT·   │
│ SLM·TTS) / local(SQLite FTS5, Phase1 기본 RAG) / sync       │
├───────────────────────────────────────────────────────────┤
│ 서버(온프레미스, 모듈러 모놀리스 우선 — v0.4 정정):          │
│   services/{author,care,schedule}-engine, sync-gateway,     │
│   rag-core는 논리적 구분이며, 첫 커밋은 api/worker 2프로세스│
│   모듈러 모놀리스로 시작 (CTO Enterprise B3, design.md §11) │
├───────────────────────────────────────────────────────────┤
│ 웹 콘솔: apps/web (가족·자서전 사용자), apps/admin (관리자) │
└───────────────────────────────────────────────────────────┘

> AWS EKS/Terraform 등 bkit Enterprise 기본 인프라 템플릿은 그대로
> 적용하지 않고, 온프레미스 K8s/베어메탈 GPU 클러스터로 대체 확정
> (structure.md, CONVENTIONS.md §1.2 참조 — v0.4: "검토 필요"에서 격상)
```

---

## 8. Convention Prerequisites

### 8.1 Existing Project Conventions

- [x] `CLAUDE.md` — 생성 완료
- [x] `CONVENTIONS.md`, `docs/01-plan/naming.md`, `structure.md` — Phase 2 완료
- [ ] ESLint/Prettier/ruff/ktlint 등 실제 설정 파일 — 미작성 (Do 단계, 코드베이스 착수 시)

### 8.2 Conventions to Define/Verify

> *(v0.4 정정 — 3차 검증 M-5: 아래 4항목 모두 Phase 2/4에서 이미 정의 완료됐으나 "missing"으로 남아있던 자기모순을 해소)*

| Category | Current State | Defined In | Priority |
|----------|---------------|-----------|:--------:|
| 서비스/모듈 네이밍 | ✅ 정의 완료 | author-engine / care-engine / schedule-engine / sync-gateway 등 — [structure.md §1](../structure.md) | High |
| 모노레포 구조 | ✅ 정의 완료 | apps/, services/, packages/(design-tokens 포함), infra/ — [structure.md](../structure.md) (7.3절은 요약만) | High |
| 온디바이스-서버 API 계약 | ✅ 정의 완료 | [sync-contract.md](../../02-design/sync-contract.md) — 비동기 업로드, 엔티티별 충돌정책, 증분 다운로드 | High |
| 환경변수 | ✅ 정의 완료 | [CONVENTIONS.md §4](../../../CONVENTIONS.md) — DB_/QDRANT_/NEO4J_/MINIO_/VLLM_/AUTH_/STT_/EMBEDDING_ 등 접두사 | Medium |

### 8.3 Pipeline Integration

| Phase | Status | Document Location | Command |
|-------|:------:|-------------------|---------|
| Phase 1 (Schema) | ✅ | [`docs/01-plan/schema.md`](../schema.md)(v1.4), [`erd.md`](../erd.md), [`glossary.md`](../glossary.md) | `/phase-1-schema` |
| Phase 2 (Convention) | ✅ | [`CONVENTIONS.md`](../../../CONVENTIONS.md), [`naming.md`](../naming.md), [`structure.md`](../structure.md) | `/phase-2-convention` |
| Phase 3 (Mockup) | ✅ | [`design-tokens.md`](../../02-design/design-tokens.md) — 컬러/타이포/접근성 최소기준 | — |
| Phase 4 (API 설계) | ✅ | [`silveryarn-platform.design.md §4`](../../02-design/features/silveryarn-platform.design.md), [`sync-contract.md`](../../02-design/sync-contract.md) | — |

---

## 9. Next Steps

1. [x] Design 문서 작성 (`silveryarn-platform.design.md`) — 본 등록 작업에서 초안 작성 완료
2. [x] 원본 기획서 9장 미결 사항 1차 정리 — 14개 중 11개 확정/보류 처리, 3개는 법무·경영 검토 필요로 분류 ([decisions.md](../decisions/silveryarn-platform.decisions.md))
3. [x] `/phase-1-schema`로 엔티티 정식 스키마 정의 완료, 3차 design-validator까지 반영한 현재 v1.4(17개 엔티티) ([schema.md](../schema.md), [glossary.md](../glossary.md))
4. [x] `/phase-2-convention`으로 서버(Python)·모바일(Kotlin)·웹(TS) 컨벤션 확정 ([CONVENTIONS.md](../../../CONVENTIONS.md))
5. [x] `design-validator` 에이전트로 기획서·프로세스흐름도·UI/UX 3개 원본 문서 간 정합성 검증 완료, High+Medium 23건 및 원본 문서 오류 7건 수정 완료 (2026-09-05)
6. [ ] 온프레미스 인프라(K8s/베어메탈 GPU 클러스터) 설계 — infra-architect 상담
7. [ ] 정서 모니터링 알림의 법적/윤리적 기준 — 법무·윤리 검토 착수 (decisions.md #12)
8. [ ] Phase 1(MVP) 착수 일정·예산·인력 — 경영진 승인 대기 (decisions.md #14)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-09-05 | Plan/ 폴더 원본 기획서(v0.5) 기반 초안 등록 | NUBiz AX Initiative |
| 0.2 | 2026-09-05 | design-validator 1차 검증(33건) 반영, decisions.md #1~#23 의사결정 로그 연동, 스택 확정사항(FastAPI/Next.js/Keycloak) 동기화 | NUBiz AX Initiative |
| 0.3 | 2026-09-07 | 2차 design-validator 검증 반영 — Vector DB/Neo4j 행 추가(§7.2), 챕터윤문 LLM 확정 행 추가, 정서모니터링 In Scope/FR-07에 Phase 1 OFF 명시(M-10), "경량VectorDB"→FTS5 표현 정정(M-8) | NUBiz AX Initiative |
| 0.4 | 2026-09-07 | 3차 design-validator 검증 반영 — M-5: §7.3 마이크로서비스 표현을 모듈러 모놀리스 우선 원칙과 일치시킴, §8.2 "missing" 4항목이 실제로는 이미 정의 완료된 자기모순 해소(sync-contract.md 링크 포함), §8.3에 Phase 3/4 행 추가, §9-3 schema.md 버전 표기 "v1.1"→현재판으로 정정 | NUBiz AX Initiative |
