# 은빛실타래 (SilverYarn)

> 어르신 자서전 제작 및 AI 말벗돌봄 플랫폼 — 온디바이스(오프라인 우선) + 온프레미스 서버 하이브리드 아키텍처

---

## Core Principles

### 1. Automation First, Commands are Shortcuts
Claude automatically applies PDCA methodology. Commands are shortcuts for power users.

### 2. SoR (Single Source of Truth) Priority
```
1st: Codebase (실제 동작 코드) — 착수 전이므로 현재는 해당 없음
2nd: CLAUDE.md / docs/ PDCA 문서
3rd: Plan/ 폴더 원본 기획 산출물 (기획서·프로세스흐름도·BI가이드·UI/UX설계서)
```
코드가 존재하게 되면 코드가 항상 최우선이며, 문서와 다르면 문서를 갱신한다.

### 3. No Guessing
```
불명확 → docs/ 및 Plan/ 원본 문서 확인
문서에도 없음 → 사용자에게 질문 (특히 기획서 9장 "다음 논의가 필요한 사항")
절대 임의로 추측·확정하지 않음
```

---

## Project Level & Status

| Item | Value |
|------|-------|
| Level | **Enterprise** (온디바이스 AI + 온프레미스 GPU 서버 + 다중 마이크로서비스 + 엄격한 데이터 주권 요구) |
| PDCA Phase | **Do 진행 중** (design v0.56). PR #1~#39 — 보안 블로커 B1~B6 + 법무·인프라·경영 미결 14건(Q1~Q6·I1~I5·경영3, decisions.md #52~#65) 전부 확정+구현 완료. PR #40~#47 후속 — 문서 정합성 점검, FP 기반 SW개발비 산정, Phase 3 출판 파이프라인(`publications` 모듈), **모바일 UI 패러다임 전환**(하단 4탭 제거 → 은실이 대화 화면 하나로 통합, 실 VAD 구현, decisions.md #66~#68). 남은 후속은 온디바이스 SLM 실기기 벤치마크(#27/#9/#31, 프로토콜+하니스 준비완료, 실기기 대기)뿐 |
| 9-Phase Pipeline | Phase 1(Schema) ✅ · Phase 2(Convention) ✅ · Phase 3(Mockup, BI가이드+UI/UX설계서+design-tokens.md) ✅ · Phase 4(API 설계, sync-contract.md 포함) ✅ 완료 |
| Primary Feature | `silveryarn-platform` |
| 원본 기획 자료 | `Plan/` 폴더 (기획서 v0.5, 프로세스흐름도, BI가이드 v2.0, UI/UX설계서 v1.2) |
| PDCA 문서 | `docs/01-plan/features/silveryarn-platform.plan.md`(v0.5), `docs/02-design/features/silveryarn-platform.design.md`(v0.57), `docs/03-check/gap-analysis-2026-09-10.md`, `docs/03-check/gap-analysis-2026-09-11.md`, `docs/03-check/blocked-decisions-tracker.md`(법무·인프라·경영 14건 완료 트래커), `docs/04-report/features/silveryarn-platform.report.md` |
| 화면정의서 | `docs/02-design/screen-definitions.md`(v0.2) — 사용자 화면(UI/UX)만 기준 화면정의서, 모바일(4)·웹 사용자·가족(12)·웹 관리자(8) 총 24개 화면 전수 + 전체/영역별 Mermaid 흐름도 |
| 동기화 계약 | `docs/02-design/sync-contract.md`(v0.8) — 비동기 업로드(202+job_id), 엔티티별 충돌정책, Presigned URL, 증분 다운로드 |
| 의사결정 로그 | `docs/01-plan/decisions/silveryarn-platform.decisions.md`(v0.26) (기획서 9장 + design-validator 반영 항목 + §2.9 법무·인프라·경영 14건 #52~#65 + §2.10 모바일 UI 전환 #66~#68) |
| 디자인 토큰 | `docs/02-design/design-tokens.md`(v1.2) (BI 가이드 컬러/타이포 → Tailwind 토큰, WCAG AA 대비 규칙, 접근성 최소기준) |
| 데이터 분류 정책 | `docs/02-design/data-classification-policy.md`(v0.1, 신규) — PII/메타데이터 4단계 분류 + 외부 통신 경계(decisions.md #58/I1) |
| 발표자료 | `docs/presentations/은빛실타래_개발착수회의_kickoff.pptx` (66슬라이드), `docs/presentations/은빛실타래_설계발표_슬라이드.html` (72슬라이드 HTML, 방향키 네비게이션) — [게시 링크](https://claude.ai/code/artifact/8c0fdb75-5c19-4916-b406-eb38275f2146). 두 산출물 모두 2026-09-05 착수 시점 스냅샷 — 페르소나명("은빛이") 등 이후 변경분(#66) 미반영, 의도적으로 보존 |
| 워크플로우 다이어그램 | `docs/02-design/workflow-diagrams.md`(v0.7) — Mermaid 21종 (마스터 Closed-Loop, 분야별 프로세스, 스윔레인, 상태전이, 계정삭제·보유기간 파기 흐름 등) |
| CTO팀 검토 | `docs/02-design/cto-review-2026-09-05.md` — 7개 관점(아키텍처/인프라/보안/FE/백엔드·API/QA/PM) 착수 심사, 판정: **전원 Go with Conditions** (Blocker 28건, 전부 정책 확정 또는 구현 완료 — 실측 대기 항목만 잔존) |

> **⚠️ CTO팀 착수 심사 이력**: 초기 검토에서 Blocker 28건 발견, 그중 보안 관점 **동의·보유기간·PII암호화·인가모델 5대 법적 리스크**는 이제 전부 해소됐다(아래 요약). 상세 원본은 `docs/02-design/cto-review-2026-09-05.md` 참조(착수 시점 스냅샷 — 이후 진행 상황은 이 파일과 decisions.md가 최신).
> - 정서 모니터링 파이프라인은 **여전히 피처플래그 OFF**(제품 판단 — 법적 전제는 [decisions.md #52/#55](./docs/01-plan/decisions/silveryarn-platform.decisions.md)로 정리됐으나 기능 자체는 별도 착수 필요)
> - 6개 마이크로서비스로 첫 커밋을 찍지 말라는 권고대로 모듈러 모놀리스(`services/backend/` 단일 배포, api/worker 2프로세스)로 확정·유지 중
> - PII 암호화: 자유텍스트 5개 컬럼(1차, decisions.md #45) + `contact`/`birth_date`(2차) + blind index 키 정식 분리(3차, decisions.md #60) **전부 구현 완료**. `name`은 부분검색 UX상 의도적으로 평문 유지. KEK는 여전히 `PII_KEK` 환경변수(Vault/OpenBao 이전은 계속 보류)
> - 인증/인가: Keycloak JWKS RS256 + Device Token + RBAC/IDOR + social_worker 조건부 허용(third_party_access 동의, decisions.md #54) + B2G 시설 테넌시 안전망(decisions.md #59) **전부 구현 완료**. apps/web·apps/admin 둘 다 Keycloak 실 로그인(Auth.js)
> - 보유기간·계정 삭제(erasure): crypto-shredding + Qdrant/Neo4j/MinIO 오케스트레이션 **구현 완료**(decisions.md #56, Q5, PR #39) — 법무·인프라·경영 미결 14건의 마지막 항목이었음
> - self-hosted 관측 스택(GlitchTip+Prometheus/Grafana/Loki) **구현 완료**(decisions.md #61)
> - "PII 수준" 외부 통신 경계는 [`data-classification-policy.md`](./docs/02-design/data-classification-policy.md)로 명문화 완료(decisions.md #58)
> - **남은 것**: 온디바이스 SLM 모델 최종 선정·실시간 파이프라인 수치 검증은 실기기 벤치마크 대기(decisions.md #27/#9/#31 — 프로토콜+하니스 준비완료, 물리 기기 확보 필요)
> - 접근성 최소기준(BODY 20px 등)은 문서화 완료, 구체 구현 방식은 Do 단계 확정

> **⚠️ 중요**: bkit Enterprise 스킬의 기본 인프라 템플릿(AWS EKS/RDS/Terraform, Turborepo Next.js/FastAPI 표준 스택)은 **참고용일 뿐 그대로 적용하지 않는다.** 본 프로젝트는 Zero External Data Egress 원칙(기획서 3.1절)에 따라 **온프레미스 자체 GPU 서버(vLLM·A100)** 기반이며, 모바일은 온디바이스 STT/SLM/TTS가 필수인 네이티브(또는 이에 준하는) 앱이다. 실제 스택 확정 전까지 아래 Tech Stack 표를 우선한다.

---

## Tech Stack (확정/미정 구분)

| 영역 | 항목 | 상태 |
|------|------|------|
| 모바일 | Android 네이티브(Kotlin), Device Owner Mode(COSU)로 키오스크 구현 | ✅ 확정 |
| 온디바이스 SLM | Kanana-2, Qwen2.5-0.5B 등 경량(0.5~3B, 4bit 양자화) 후보 | **미정** (벤치마크 후보 2종 확보, 최종선정은 실기기 벤치마크 후 — decisions.md #27) |
| 온디바이스 음성 파이프라인 | WebRTC VAD(800ms 묵음판정) + 경량 STT(Sherpa-ONNX 등 후보) + **SQLite FTS5 단독 RAG(Phase 1 확정, decisions #32)** + 문장단위 스트리밍 TTS + 네이티브 TTS, 원본음성 Opus(16kbps) 압축·업로드성공시 즉시삭제(#30) | 🔄 구조·기법 확정, 라이브러리·수치는 Do 단계 벤치마크. **VAD만 임시 실구현**(`AmplitudeVoiceActivityDetector`, 진폭 임계값 기반, decisions #68) — WebRTC VAD 후보 자체는 여전히 벤치마크 대기, 무음판정 타이밍(800ms)만 재사용 |
| 온디바이스 로컬 스키마 | Room/SQLite 6개 테이블 (`conversations`, `autobiography_fts` 등) | ✅ 초안 확정 — [mobile-schema.md](./docs/01-plan/mobile-schema.md) |
| 데이터 모델링 & ERD | 서버 도메인 19개 엔티티(+부속 4개) + 온디바이스 6개 테이블 관계도 (흑백 Mermaid, 도메인별 3분할) | ✅ [erd.md](./docs/01-plan/erd.md) |
| 서버 백엔드 | 자체 호스팅 Python 3.11+ / **FastAPI** | ✅ 확정 (decisions.md #15) |
| LLM 추론 | 자체 호스팅 vLLM · A100 GPU 서버 | ✅ 확정 |
| Vector DB | Qdrant self-hosted (하이브리드 서치 BM25+Dense) | ✅ 확정 (Milvus 제안 검토했으나 미채택, decisions.md #28) |
| 지식 그래프 | Neo4j self-hosted — 인물·사건·감정 엔티티 관계 추적 | ✅ 확정 (decisions.md #29, 신규) |
| RDB | PostgreSQL | ✅ 확정 |
| Object Storage | 자체 MinIO | ✅ 확정 |
| 임베딩 모델 | BGE-M3 계열 (한국어 다국어 임베딩) | ✅ 확정 |
| 웹 콘솔 프론트엔드 | Next.js(App Router)+TypeScript+Tailwind | ✅ 확정 (Phase 2, CONVENTIONS.md §0.1) |
| 인프라 호스팅 | **온프레미스** K8s/베어메탈 GPU 클러스터 (AWS 아님) | ✅ 확정 (구체 구성 미정) |
| 인증 | **Keycloak SSO** | ✅ 확정 (decisions.md #17 — 원본 프로세스흐름도 §4.1과 정합) |

---

## Development Workflow

> 코드베이스 착수 전이라 아래는 CONVENTIONS.md 기준 예정 명령이며, 실제 `package.json`/`pyproject.toml`/`build.gradle.kts` 작성 시(Do 단계) 확정된다.

```bash
# 서버 (services/{engine}, Python/FastAPI)
ruff check . && ruff format --check .   # Lint
mypy .                                    # Type check
pytest                                    # Test
alembic upgrade head                      # DB 마이그레이션

# 웹 콘솔 (apps/web, apps/admin, Next.js)
npm run lint
npm run type-check
npm run build

# 모바일 (apps/mobile, Kotlin)
./gradlew ktlintCheck
./gradlew test
./gradlew assembleDebug
```

---

## Term Reference

프로젝트 용어 정의는 `docs/01-plan/glossary.md`에서 통합 관리한다. 비즈니스 용어를 코드/문서에 사용할 때 항상 참조할 것. 데이터 엔티티 정식 스키마는 `docs/01-plan/schema.md` 참조.

---

## Coding Conventions

Phase 2 완료 — 정식 컨벤션은 [`CONVENTIONS.md`](./CONVENTIONS.md) 참조 (서버 Python/FastAPI, 모바일 Kotlin, 웹 Next.js 스택별 네이밍·폴더구조·환경변수 규칙 포함). 상세는 [`docs/01-plan/naming.md`](./docs/01-plan/naming.md), [`structure.md`](./docs/01-plan/structure.md).

- 온프레미스 GPU 서버·DB·오브젝트스토리지 접속 정보는 절대 하드코딩 금지, 시크릿 매니저/환경변수 사용 (CONVENTIONS.md §4)

---

## Project Structure (제안 — Design 문서 §11.1 기준, 아직 스캐폴딩 전)

```
silveryarn/
├── apps/
│   ├── mobile/            # 온디바이스 앱 (설치모드 자동분기: 키오스크/일반)
│   ├── web/                # 자서전 사용자·가족 웹 콘솔
│   └── admin/               # 관리자 콘솔
├── services/
│   ├── gateway/             # API Gateway/오케스트레이터
│   ├── author-engine/       # 자서전 작가 모드
│   ├── care-engine/         # 말벗돌봄 모드
│   ├── schedule-engine/     # 비서 모드 (일정/복약)
│   ├── sync-gateway/        # Wi-Fi 배치 동기화
│   ├── rag-core/            # LLM·임베딩·Vector DB 오케스트레이션
│   └── shared/               # 공통 유틸·Alembic 마이그레이션만 (도메인 로직 없음)
├── packages/
│   └── py-common/            # 서비스 간 공유 Python 패키지
├── infra/                   # 온프레미스 K8s/베어메탈 GPU 클러스터
├── docs/                    # PDCA 문서 (01-plan ~ 04-report)
└── Plan/                    # 원본 기획 산출물 (기획서/흐름도/BI/UIUX) — 보존, 수정 시 문서관리팀 확인
```

---

## PDCA Auto Behavior

### On New Feature Request
```
1. docs/02-design/ 확인 → 없으면 design 문서부터 생성
2. 기획서 9장 미결 사항과 충돌하는지 확인 → 충돌 시 사용자에게 확인
3. Design 기반으로 구현
4. 완료 후 Gap 분석 제안
```

### On Bug Fix / Refactoring
```
1. 코드와 docs/ 설계 문서 비교
2. 원인 파악 후 수정
3. 문서 갱신 제안
```

---

## Key Commands

| Command | Description |
|---------|-------------|
| `/pdca status` | 현재 PDCA 상태 확인 |
| `/phase-1-schema` | Device/User/Chapter/Photo 등 엔티티 정식 스키마 정의 |
| `/phase-2-convention` | 코딩 컨벤션 확정 |
| `/pdca design silveryarn-platform` | Design 문서 갱신 |

---

## 의사결정 현황 (기획서 9장 — 상세는 `docs/01-plan/decisions/silveryarn-platform.decisions.md`)

**확정됨** (임의 변경 금지, 변경 시 decisions.md 갱신 필수):
- 설치모드 임계값: RAM<6GB 또는 Android≤11 → 키오스크
- 키오스크 구현: Device Owner Mode(COSU), Screen Pinning 미채택
- 모바일: Android 네이티브(Kotlin) 전용
- Wi-Fi 동기화: 등록 Wi-Fi 한정, 접속 즉시 자동 트리거, 데이터 제한 없음
- 사진 업로드 UX: 카메라 촬영+갤러리 선택 모두 지원, 클라이언트 리사이즈/압축
- 사진 인라인 편입: AI 삽입은 항상 제안 상태, 가족이 웹콘솔에서 최종 조정
- 채널: B2C/B2G 병행 추진
- 외부 TTS: Phase 1~2는 온프레미스만, 외부연계는 Phase 3로 유예
- '기억의 서재'와는 완전 별개 프로젝트
- 서버 백엔드: Python/FastAPI, 웹 콘솔: Next.js, 인증: Keycloak SSO
- 구독·결제 도메인: Phase 1 스코프 아웃 (PG사·요금제는 경영 결정 대기)
- API 응답 케이싱은 snake_case, DB enum 값은 영문 통일(표시명은 schema.md §7 매핑)
- Wi-Fi 등록정보(SSID 등)는 온디바이스 로컬 전용, 서버 미저장
- **법무·인프라·경영 미결 14건**(2026-09-12 사용자 결정, decisions.md #52~#65, 전부 구현 완료 2026-09-13): 정서점수는 일반개인정보로 별도동의 불필요(#52)·가족 대리동의 유효(#53)·가족=위탁이용/복지사=제3자제공(#54)·정서기능 "진단" 표현 회피(#55)·crypto-shredding 파기채택+보유기간 admin 설정(#56)·FCM 유지+국외이전고지(#57)·PII만 egress 차단(#58)·B2G 시설 테넌시는 안전망 스코프로 착수(#59)·blind index 키만 우선 분리(#60)·self-hosted 관측스택 구축(#61)·서버LLM 비실시간전용(#62)·3개월 파일럿 목표(#63)·결제도메인 스코프아웃 유지(#64)·외부TTS Phase3 유예(#65). 법무 6건(Q1~Q6)은 정식 외부 법률자문을 대체하지 않는 잠정 회사 정책임에 유의

**여전히 미결 — 반드시 임의 결정 금지** (위 14건과 무관한 별도 트랙, 실측·경영 후속 성격):
- 정서 모니터링 알림의 **구체 임계치 로직**(언제 발송할지) ⚖️ 여전히 법무·윤리 검토 필요(decisions.md #19) — 법적 분류(#52/#55)와는 별개 질문
- 외부 TTS 구체 벤더·비용·DPA ⚖️ Phase 3 유예 재확인(#65)됐을 뿐 벤더 자체는 미정
- Phase 1~3 정식 예산·인력 ⚖️ "3개월 파일럿" 목표(#63)만 확정, 경영진의 정식 승인은 여전히 대기
- 온디바이스 SLM 모델 자체 선정 (Kanana-2 등) — 실기기 벤치마크 대기(#27, 프로토콜+하니스 준비완료)
- 로컬 "최근 5일" 캐시 기준 — 기본값 유지, 실기기 벤치마크 후 재확정(#9)

---

**Generated by**: bkit Enterprise 초기화 (`/enterprise init`) — Plan/ 폴더 원본 기획 산출물 편입
**Template Version**: 1.3.0 기반, 프로젝트 특성에 맞게 커스터마이즈
