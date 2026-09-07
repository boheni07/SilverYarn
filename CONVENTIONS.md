# silveryarn-platform Coding Conventions

> **Phase 2 Deliverable**: 코딩 규칙 정의
>
> **Project**: 은빛실타래 (SilverYarn)
> **Date**: 2026-09-05
> **Version**: 1.0
> **Level**: Enterprise (다중 스택 — 서버/모바일/웹 콘솔)

> 본 프로젝트는 단일 스택이 아니라 **온프레미스 서버(Python)** + **온디바이스 모바일(Kotlin)** + **웹 콘솔(TypeScript)**의 3중 스택이므로, 영역별로 컨벤션을 분리 정의한다. 상세 네이밍은 [`docs/01-plan/naming.md`](./docs/01-plan/naming.md), 폴더 구조는 [`docs/01-plan/structure.md`](./docs/01-plan/structure.md) 참조.

---

## 0. 스택별 적용 범위

| 영역 | 스택 | 대상 |
|---|---|---|
| 서버 (`services/*`) | Python 3.11+ / FastAPI | author-engine, care-engine, schedule-engine, sync-gateway, rag-core, gateway |
| 모바일 (`apps/mobile`) | Kotlin (Android 네이티브) | 온디바이스 앱 — decisions.md #7 확정 |
| 웹 콘솔 (`apps/web`, `apps/admin`) | TypeScript / Next.js (App Router) | 자서전 사용자·가족·관리자 콘솔 — **본 문서에서 확정** (아래 §0.1) |
| DB | PostgreSQL, 마이그레이션: **Alembic** | 서버가 Python이므로 Python 생태계 도구로 통일 |

### 0.1 웹 콘솔 프레임워크 확정

Plan 문서(§7.2)에 "미정"으로 남아있던 웹 콘솔 프레임워크를 **Next.js(App Router) + TypeScript + Tailwind CSS**로 확정한다. 근거: bkit 표준 스택과의 정합성, 가족/관리자 대시보드 성격상 SSR·라우팅 편의성이 유리, 온프레미스 배포(Node 컨테이너)와도 호환. *(이 결정은 인프라 주권·법적 사안과 무관한 통상적 기술 선택으로, 별도 승인 없이 확정 — 필요 시 언제든 재검토 가능)*

---

## 1. 서버 (Python/FastAPI) 컨벤션

### 1.1 네이밍

| 대상 | 규칙 | 예시 |
|---|---|---|
| 모듈/파일 | snake_case | `author_engine.py`, `sync_gateway.py` |
| 클래스 | PascalCase | `ChapterService`, `PhotoRepository` |
| 함수/변수 | snake_case | `get_chapter_by_id()`, `raw_audio_ref` |
| 상수 | UPPER_SNAKE_CASE | `MAX_SYNC_RETRY`, `KIOSK_RAM_THRESHOLD_GB` |
| Pydantic 모델(DTO) | PascalCase + 접미사 | `ChapterCreateRequest`, `ChapterResponse` |

### 1.2 Clean Architecture 레이어 (Design 문서 §9와 동일)

```
services/{engine}/
├── api/            # Presentation — FastAPI 라우터, 요청/응답 DTO
├── application/    # Application — 유스케이스, 서비스 클래스
├── domain/         # Domain — 순수 엔티티·비즈니스 규칙 (schema.md 기반)
└── infrastructure/ # Infrastructure — SQLAlchemy, Qdrant client, MinIO client, vLLM client
```

의존 방향: `api → application → domain ← infrastructure` (domain은 외부 의존성 없음).

### 1.3 코드 스타일

- 포맷터: `ruff format` (또는 `black`), 린터: `ruff`
- 타입 힌트 필수 (함수 시그니처 전체) — `mypy` 검사 권장
- Docstring: Google 스타일
- 비동기 I/O 기본 (`async def`), DB는 SQLAlchemy 2.0 async

### 1.4 DB 마이그레이션

**Alembic** 채택 확정 — 백엔드가 Python/FastAPI이므로 동일 생태계 도구로 통일. 마이그레이션 파일은 `services/shared/infrastructure/migrations/`에 위치.

### 1.5 테스트

`pytest` + `pytest-asyncio`. 서비스별 `tests/` 디렉토리, Design 문서 §8 Test Plan의 L1(API) 시나리오를 여기서 구현.

---

## 2. 모바일 (Kotlin/Android) 컨벤션

### 2.1 네이밍

| 대상 | 규칙 | 예시 |
|---|---|---|
| 패키지 | 소문자, 역도메인 | `com.silveryarn.mobile.ondevice` |
| 클래스/컴포저블 | PascalCase | `ChapterInterviewScreen`, `SyncWorker` |
| 함수/변수 | camelCase | `startVoiceSession()`, `unrecalledPhotoQueue` |
| 상수 | UPPER_SNAKE_CASE | `RAM_THRESHOLD_GB`, `SYNC_RETRY_MAX` |
| 리소스 파일 | snake_case | `ic_microphone.xml` |

### 2.2 모듈 구조 (Design 문서 §9.1과 매핑)

```
apps/mobile/
├── presentation/     # UI (Jetpack Compose), 대화 화면, 사진 업로드 UI
├── ondevice/         # VAD·STT·SLM·TTS, 온디바이스 라우터
├── local/            # Room(SQLite, FTS5 가상테이블), 경량 VectorDB, 동기화 클라이언트
├── installmode/      # 설치모드 자동분기 로직 (Device Owner Mode 프로비저닝)
└── sync/             # Wi-Fi 배치 동기화 워커 (WorkManager)
```

### 2.2.1 온디바이스 음성 파이프라인 구현 후보 (Design 문서 §2.11 반영, v1.1 신규)

| 구성요소 | 후보 라이브러리/포맷 | 상태 |
|---|---|---|
| VAD | WebRTC VAD | 후보 — Do 단계 확정 |
| STT | Sherpa-ONNX 등 경량 온디바이스 엔진 | 후보 |
| SLM | Kanana-2, Qwen2.5-0.5B (4bit 양자화) | 벤치마크 후보 2종 — [decisions.md #27](./docs/01-plan/decisions/silveryarn-platform.decisions.md) |
| TTS | Android 네이티브 TTS | 후보 |
| 로컬 RAG | **SQLite FTS5(BM25 키워드) 단독 — Phase 1 기본값** ([decisions.md #32](./docs/01-plan/decisions/silveryarn-platform.decisions.md)) | 확정(구조). 경량 VectorDB(임베딩)는 고사양 단말 한정 Phase 2+ 검토 |
| 원본 음성 압축 | Ogg/Opus 16kbps | 제안 반영 — 서버 업로드 성공 시 로컬 원본 즉시 삭제([decisions.md #30](./docs/01-plan/decisions/silveryarn-platform.decisions.md)) |
| VAD 묵음판정 윈도우 | 800ms | 확정(기법) — [decisions.md #31](./docs/01-plan/decisions/silveryarn-platform.decisions.md) |
| SLM→TTS 스트리밍 | 문장 단위 슬라이싱 후 즉시 TTS 파이프라이닝(전체 응답 대기 없음) | 확정(기법) — [decisions.md #31](./docs/01-plan/decisions/silveryarn-platform.decisions.md) |
| 로컬 스키마 | Room/SQLite 테이블 정의 | [mobile-schema.md](./docs/01-plan/mobile-schema.md) 참조 (신규) |

### 2.3 코드 스타일

- 린터: `ktlint`, 공식 Kotlin 스타일 가이드 준수
- UI: Jetpack Compose, `@Composable` 함수는 PascalCase 명사형
- 백그라운드 작업: `WorkManager` (동기화·알림 예약)

---

## 3. 웹 콘솔 (TypeScript/Next.js) 컨벤션

bkit 표준 컨벤션을 그대로 따른다 (`CLAUDE.md` 및 아래 요약 참조).

### 3.1 네이밍

| 대상 | 규칙 | 예시 |
|---|---|---|
| 컴포넌트 파일 | PascalCase | `ChapterReviewPanel.tsx` |
| 유틸 파일 | camelCase | `formatSyncStatus.ts` |
| 폴더 | kebab-case | `chapter-review/` |
| 함수/변수 | camelCase | `getChapterById()` |
| 상수 | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE_MB` |
| 타입/인터페이스 | PascalCase | `ChapterDto`, `EmotionAlert` |

### 3.2 폴더 구조 (Enterprise)

```
apps/web/src/
├── presentation/     # components/, hooks/, app/
├── application/      # services/, use-cases/
├── domain/           # types/ (schema.md 엔티티와 1:1 매핑)
└── infrastructure/   # lib/api/ (서버 API 클라이언트)
```

### 3.3 임포트 순서

```typescript
// 1. External libraries
import { useState } from 'react'
// 2. Internal absolute imports
import { Button } from '@/components/ui'
// 3. Relative imports
import { useChapterReview } from './hooks'
// 4. Type imports
import type { Chapter } from '@/domain/types'
// 5. Styles
import './styles.css'
```

---

## 4. 환경변수 컨벤션 (온프레미스 스택 기준)

> bkit 표준의 `NEXT_PUBLIC_/DB_/API_/AUTH_` 접두사에 더해, 온프레미스 AI 인프라 전용 접두사를 추가한다.

| Prefix | 용도 | 노출 범위 | 예시 |
|--------|------|:---:|------|
| `NEXT_PUBLIC_` | 웹 클라이언트 노출 | Browser | `NEXT_PUBLIC_API_URL` |
| `DB_` | PostgreSQL 접속 | Server only | `DB_HOST`, `DB_PASSWORD` |
| `STORAGE_` | MinIO Object Storage | Server only | `STORAGE_ENDPOINT`, `STORAGE_SECRET_KEY` |
| `VECTORDB_` | Qdrant 접속 | Server only | `VECTORDB_HOST`, `VECTORDB_API_KEY` |
| `GRAPH_` | Neo4j 지식그래프 접속 (신규) | Server only | `GRAPH_URI`, `GRAPH_PASSWORD` |
| `LLM_` | vLLM 추론 서버 | Server only | `LLM_ENDPOINT`, `LLM_MODEL_NAME` |
| `AUTH_` | 인증(SSO 등) | Server only | `AUTH_SECRET` *(SSO 공급자는 미정 — Keycloak 후보)* |
| `SYNC_` | 배치 동기화 파라미터 | Server only | `SYNC_MAX_RETRY`, `SYNC_CHECKSUM_ALGO` |

```
⚠️ 보안 원칙
- NEXT_PUBLIC_* 외 어떤 것도 클라이언트에 노출 금지
- 온프레미스 시크릿(DB/Storage/LLM/VectorDB 접속정보)은 시크릿 매니저(구체 도구는 인프라 설계에서 확정) 경유, .env 파일에 평문 커밋 금지
- 원본 구술 음성·전사 텍스트 등 PII는 환경변수가 아닌 schema.md §5 암호화 정책(Do 단계 확정)을 따름
```

### 4.1 모바일(Kotlin) 시크릿 관리 — v1.1 신규 (design-validator F-7)

모바일은 `.env` 대신 Gradle `BuildConfig` 필드 또는 `local.properties`(Git 제외)로 빌드 타임 상수를 주입한다. 서버 API 엔드포인트 등 민감하지 않은 값만 `BuildConfig`에 두고, 기기별 동적 값(설치모드 등)은 Room DB에 런타임 저장한다.

```kotlin
// app/build.gradle.kts
buildConfigField("String", "API_BASE_URL", "\"${localProperties["API_BASE_URL"]}\"")
```

### 4.2 .env 파일 구조

```
project-root/
├── .env.example        # 템플릿 (Git 포함)
├── .env.local           # 로컬 개발 (Git 제외)
├── .env.development
├── .env.staging
└── .env.production      # 민감정보 없음, 온프레미스 시크릿 매니저 참조만
```

---

## 4.3 API 표준 (Design 문서 §4 참조 — v1.1 신규)

API 응답 포맷·표준 에러 코드·버전 프리픽스(`/api/v1`)는 [design.md §4.1](./docs/02-design/features/silveryarn-platform.design.md)에서 확정했다. 필드 케이싱은 서버 snake_case, 클라이언트는 각 스택 컨벤션(웹 camelCase, Kotlin camelCase)으로 변환한다.

## 4.4 디자인 토큰 (v1.1 신규)

BI 가이드의 컬러·타이포는 [design-tokens.md](./docs/02-design/design-tokens.md)에서 Tailwind 토큰으로 매핑했다. 웹/모바일 모두 색상 리터럴 하드코딩 금지 — 토큰(클래스/상수)만 사용.

---

## 5. Phase Connection

| 정의 (Phase 2) | 검증 (Phase 8) |
|---|---|
| 서버/모바일/웹 네이밍 규칙 | 네이밍 일관성 점검 |
| 서비스별 Clean Architecture 폴더 구조 | 구조 일관성·의존방향 점검 |
| 환경변수 접두사 규칙 | 환경변수 네이밍 점검 |
| Alembic/ktlint/ruff 등 도구 | Lint/CI 통과 여부 |

---

## 6. Validation Checklist

### 네이밍/구조
- [x] 서버(Python)·모바일(Kotlin)·웹(TypeScript) 네이밍 규칙 정의
- [x] 서비스별 Clean Architecture 폴더 구조 정의 (Design 문서 §9와 정합)
- [ ] Lint 설정 파일 실제 작성 (`.ruff.toml`, `.editorconfig`, `ktlint` 설정, `.eslintrc`) — Do 단계

### 환경변수
- [x] 접두사 규칙 정의 (NEXT_PUBLIC_/DB_/STORAGE_/VECTORDB_/LLM_/AUTH_/SYNC_)
- [ ] `.env.example` 실제 작성 — Do 단계 (서비스 확정 후)
- [ ] 시크릿 관리 도구 확정 — 인프라 설계(infra-architect) 단계

### 아키텍처
- [x] 레이어 구조 확정 (Enterprise, 서비스별 적용)
- [x] 의존 방향 규칙 정의 (Design 문서 §9.2와 동일)

---

## 7. Next Steps

Phase 3: Mockup — 이미 `Plan/은빛실타래_UIUX_화면설계서.html`(v1.2), `Plan/은빛실타래_BI가이드_v2.html`(v2.0)로 원본 산출물 존재. `design-validator`로 본 컨벤션·스키마 대비 정합성 확인 후 Phase 3는 "완료"로 처리 가능.

---

## Related Documents

- Naming 상세: [docs/01-plan/naming.md](./docs/01-plan/naming.md)
- Structure 상세: [docs/01-plan/structure.md](./docs/01-plan/structure.md)
- Schema: [docs/01-plan/schema.md](./docs/01-plan/schema.md)
- Glossary: [docs/01-plan/glossary.md](./docs/01-plan/glossary.md)
- Design: [docs/02-design/features/silveryarn-platform.design.md](./docs/02-design/features/silveryarn-platform.design.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-09-05 | Phase 2 — 서버/모바일/웹 3중 스택 컨벤션 초안 확정 | NUBiz AX Initiative |
| 1.1 | 2026-09-05 | design-validator 검증 반영 — 모바일 시크릿 관리(§4.1), API 표준·디자인 토큰 참조(§4.3~4.4) 추가 | NUBiz AX Initiative |
| 1.2 | 2026-09-06 | Closed-Loop 프로세스 제안 반영 — 온디바이스 음성 파이프라인 후보(§2.2.1), Neo4j `GRAPH_` 환경변수 접두사 추가 | NUBiz AX Initiative |
| 1.3 | 2026-09-06 | 실시간 대화 파이프라인 최적화 제안 반영 — FTS5 단독 RAG를 Phase 1 기본값으로 확정(§2.2.1), VAD/TTS 스트리밍 기법 추가, mobile-schema.md 신규 참조 | NUBiz AX Initiative |
