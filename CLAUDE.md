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
| PDCA Phase | Design (v0.6, design-validator 검증 3회 완료 — 74→82→87/100) — Do 단계 착수 전 |
| 9-Phase Pipeline | Phase 1(Schema) ✅ · Phase 2(Convention) ✅ · Phase 3(Mockup, BI가이드+UI/UX설계서+design-tokens.md) ✅ · Phase 4(API 설계, sync-contract.md 포함) ✅ 완료 |
| Primary Feature | `silveryarn-platform` |
| 원본 기획 자료 | `Plan/` 폴더 (기획서 v0.5, 프로세스흐름도, BI가이드 v2.0, UI/UX설계서 v1.2) |
| PDCA 문서 | `docs/01-plan/features/silveryarn-platform.plan.md`(v0.4), `docs/02-design/features/silveryarn-platform.design.md`(v0.6) |
| 동기화 계약 | `docs/02-design/sync-contract.md` — 비동기 업로드(202+job_id), 엔티티별 충돌정책, Presigned URL, 증분 다운로드 |
| 의사결정 로그 | `docs/01-plan/decisions/silveryarn-platform.decisions.md`(v0.7) (기획서 9장 + design-validator 반영 항목) |
| 디자인 토큰 | `docs/02-design/design-tokens.md`(v1.2) (BI 가이드 컬러/타이포 → Tailwind 토큰, WCAG AA 대비 규칙, 접근성 최소기준) |
| 발표자료 | `docs/presentations/은빛실타래_개발착수회의_kickoff.pptx` (66슬라이드), `docs/presentations/은빛실타래_설계발표_슬라이드.html` (72슬라이드 HTML, 방향키 네비게이션) — [게시 링크](https://claude.ai/code/artifact/8c0fdb75-5c19-4916-b406-eb38275f2146) |
| 워크플로우 다이어그램 | `docs/02-design/workflow-diagrams.md`(v0.4) — Mermaid 20종 (마스터 Closed-Loop, 분야별 프로세스, 스윔레인, 상태전이 등) |
| CTO팀 검토 | `docs/02-design/cto-review-2026-09-05.md` — 7개 관점(아키텍처/인프라/보안/FE/백엔드·API/QA/PM) 착수 심사, 판정: **전원 Go with Conditions** |

> **⚠️ Do 단계 착수 전 필수 확인**: CTO팀 검토에서 Blocker 28건 발견. 특히 보안 관점에서 **동의·보유기간·PII암호화·인가모델 5대 법적 리스크**가 발견되었으므로, `docs/02-design/cto-review-2026-09-05.md`를 반드시 먼저 읽을 것. 착수 전 요약:
> - 정서 모니터링 파이프라인은 Phase 1에서 **피처플래그로 OFF** ([decisions.md #25](./docs/01-plan/decisions/silveryarn-platform.decisions.md))
> - 온디바이스 SLM 모델 벤치마크(2주)는 예산 승인과 무관하게 즉시 착수 가능. 동기화 계약([sync-contract.md](./docs/02-design/sync-contract.md))은 3차 검증에서 작성 완료
> - 6개 마이크로서비스로 첫 커밋을 찍지 말 것 — 모듈러 모놀리스(api/worker 2프로세스) 권고
> - PII 암호화: 자유텍스트 5개 컬럼(`body_text`·`body_text_snapshot`·`transcript_*`·`assistant_response`)은 **1차 구현 완료** — 애플리케이션 레벨 필드 암호화 + 사용자별 DEK([decisions.md #45](./docs/01-plan/decisions/silveryarn-platform.decisions.md), `services/backend/src/core_service/core/crypto.py`, 마이그레이션 `0002`). `name`·`contact`·`birth_date`는 2차 라운드(부분검색 재설계·blind index·타입변경 선행). KEK는 `PII_KEK` 환경변수(Vault 이전 전까지 임시)
> - 인증/PII 암호화: **실 구현 + 실 인프라 e2e 완료** (PR #1~#8, 마이그레이션 `0002`~`0006`). Keycloak JWKS RS256 + `keycloak_sub` 매핑 + Device Token(`device_credentials` SHA-256) + `access_logs` + `authorize_user_access` RBAC/IDOR + social_worker fail-closed(#48) + PII 1·2차 암호화(`chapters.body_text` 등 + `contact` blind index + `birth_date`, name은 평문). 로컬 Keycloak realm은 `infra/keycloak/`, e2e는 `services/backend/scripts/e2e_*.py`. **남은 것**: `organizations` B2G 테넌시·retention 정책(법무 대기), `PII_KEK` Vault 이전
> - 접근성 최소기준(BODY 20px 등)은 문서화 완료, 구체 구현 방식은 Do 단계 확정

> **⚠️ 중요**: bkit Enterprise 스킬의 기본 인프라 템플릿(AWS EKS/RDS/Terraform, Turborepo Next.js/FastAPI 표준 스택)은 **참고용일 뿐 그대로 적용하지 않는다.** 본 프로젝트는 Zero External Data Egress 원칙(기획서 3.1절)에 따라 **온프레미스 자체 GPU 서버(vLLM·A100)** 기반이며, 모바일은 온디바이스 STT/SLM/TTS가 필수인 네이티브(또는 이에 준하는) 앱이다. 실제 스택 확정 전까지 아래 Tech Stack 표를 우선한다.

---

## Tech Stack (확정/미정 구분)

| 영역 | 항목 | 상태 |
|------|------|------|
| 모바일 | Android 네이티브(Kotlin), Device Owner Mode(COSU)로 키오스크 구현 | ✅ 확정 |
| 온디바이스 SLM | Kanana-2, Qwen2.5-0.5B 등 경량(0.5~3B, 4bit 양자화) 후보 | **미정** (벤치마크 후보 2종 확보, 최종선정은 실기기 벤치마크 후 — decisions.md #27) |
| 온디바이스 음성 파이프라인 | WebRTC VAD(800ms 묵음판정) + 경량 STT(Sherpa-ONNX 등 후보) + **SQLite FTS5 단독 RAG(Phase 1 확정, decisions #32)** + 문장단위 스트리밍 TTS + 네이티브 TTS, 원본음성 Opus(16kbps) 압축·업로드성공시 즉시삭제(#30) | 🔄 구조·기법 확정, 라이브러리·수치는 Do 단계 벤치마크 |
| 온디바이스 로컬 스키마 | Room/SQLite 6개 테이블 (`conversations`, `autobiography_fts` 등) | ✅ 초안 확정 — [mobile-schema.md](./docs/01-plan/mobile-schema.md) |
| 데이터 모델링 & ERD | 서버 17개 엔티티 + 온디바이스 6개 테이블 관계도 (흑백 Mermaid, 도메인별 3분할) | ✅ [erd.md](./docs/01-plan/erd.md) |
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

**여전히 미결 — 반드시 임의 결정 금지**:
- 정서 모니터링 알림의 법적/윤리적 기준 ⚖️ 법무·윤리 검토 필요
- 외부 TTS 구체 벤더·비용·DPA ⚖️ Phase 3 시점 법무 검토
- Phase 1~3 착수 일정/예산/인력 ⚖️ 경영진 승인 대기
- 온디바이스 SLM 모델 자체 선정 (Kanana-2 등)
- 로컬 "최근 5일" 캐시 기준 — 기본값 유지, 실기기 벤치마크 후 재확정

---

**Generated by**: bkit Enterprise 초기화 (`/enterprise init`) — Plan/ 폴더 원본 기획 산출물 편입
**Template Version**: 1.3.0 기반, 프로젝트 특성에 맞게 커스터마이즈
