# Folder Structure Rules

> Phase 2 Deliverable — 모노레포 전체 구조 (Design 문서 §11.1을 실행 가능한 수준으로 구체화)

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-07 · **Version**: 1.4

---

## 1. 모노레포 최상위 구조

> **v1.4 — Do 단계 착수 반영 (decisions.md #44)**: 아래 `services/`는 더 이상 "6개 마이크로서비스 제안"이 아니라 **`services/backend/` 단일 배포 단위(모듈러 모놀리스)** 로 확정됐다. `author-engine`/`care-engine`/`schedule-engine`/`sync-gateway`/`rag-core`는 이제 별도 서비스 폴더가 아니라 `services/backend/src/core_service/modules/{author,care,schedule,sync,...}/`의 **논리적 모듈**로 존재한다 — CTO Enterprise B3(6개 마이크로서비스로 첫 커밋 금지) 반영.

```
silveryarn/
├── apps/
│   ├── mobile/               # Kotlin, Android 네이티브 (온디바이스) — 아직 스캐폴딩 전
│   ├── web/                   # Next.js — 자서전 사용자·가족 웹 콘솔 — 아직 스캐폴딩 전
│   └── admin/                  # Next.js — 관리자 콘솔 — 아직 스캐폴딩 전
├── services/
│   └── backend/                 # 모듈러 모놀리스 단일 배포 단위 (Python/FastAPI) — v1.4 신규 스캐폴딩
│       ├── pyproject.toml
│       ├── alembic.ini
│       ├── migrations/            # Alembic 마이그레이션 (schema.md DDL 1:1)
│       │   └── versions/
│       ├── src/core_service/
│       │   ├── main.py             # FastAPI app 진입점 (api 프로세스)
│       │   ├── worker.py           # 비동기 잡 워커 진입점 (arq, sync-contract.md §2)
│       │   ├── core/                # config·db·logging·표준 에러 포맷(design.md §4.1)
│       │   ├── modules/             # 도메인 모듈 — 상세는 §2
│       │   │   ├── users/ devices/    # 구현 완료 (참조 패턴)
│       │   │   └── author/ care/ schedule/ sync/  # 골격만 (Phase 2+ 구현 예정)
│       │   └── shared/              # 모듈 간 공유 커널(공통 예외 등, 도메인 엔티티 아님)
│       └── tests/
├── packages/                   # 서버 서비스 간 공유 코드 (Python 패키지) + 크로스플랫폼 자산 — 아직 스캐폴딩 전
│   ├── py-common/                # 공통 유틸·인프라 헬퍼 (도메인 엔티티는 각 모듈 domain/에 위치 — F-2, §2 주석 참조)
│   └── design-tokens/            # 디자인 토큰 단일소스(JSON) → 웹 Tailwind config·모바일 Kotlin Color object 빌드 산출 (CONVENTIONS §4.4, M-7/FE-B2)
├── infra/                      # 온프레미스 K8s/베어메탈 GPU 클러스터 (AWS 템플릿 미적용)
│   ├── k8s/                      # 아직 스캐폴딩 전 — infra-architect 상담 대기
│   │   ├── base/
│   │   └── overlays/
│   └── docker-compose.yml       # 로컬 개발용 — v1.4 신규 (Postgres/Redis/Qdrant/Neo4j/MinIO)
├── docs/                        # PDCA 문서 (01-plan ~ 04-report)
├── Plan/                        # 원본 기획 산출물 (보존, 수정 시 확인 필요)
├── CLAUDE.md
├── CONVENTIONS.md
└── .env.example
```

---

## 2. 서버 내부 구조 (Python/FastAPI, `services/backend/` 모듈러 모놀리스) — v1.4 정정

> ⚠️ **정정 사유(Do 단계 착수, decisions.md #44)**: 아래는 원래 "서비스당 반복되는 패턴"이었으나, 첫 커밋은 `services/backend/` **단일 배포 단위**로 확정했다. 대신 이 4계층 패턴을 **도메인 모듈 단위**(`modules/{module}/`)로 반복해 향후 특정 모듈만 분리 배포할 여지를 남긴다.

```
services/backend/src/core_service/
├── main.py                    # FastAPI app 진입점 (api 프로세스) — 모든 모듈 라우터를 마운트
├── worker.py                  # 비동기 잡 워커 진입점 (arq) — sync-contract.md §2 잡 큐 처리
├── core/                       # 횡단 관심사 — 모듈에 속하지 않음
│   ├── config.py                 # Pydantic Settings, CONVENTIONS §4 접두사(DB_/STORAGE_/VECTORDB_/GRAPH_/...)
│   ├── db.py                     # SQLAlchemy 2.0 async engine/session
│   ├── errors.py                  # 표준 에러 포맷(design.md §4.1) + 예외 핸들러
│   └── logging.py
├── modules/{module}/            # 도메인 모듈 (users, devices, author, care, schedule, sync ...)
│   ├── api/v1/{resource}.py         # Presentation — FastAPI 라우터, Pydantic DTO
│   ├── application/{resource}_service.py  # Application — 유스케이스, 서비스 클래스
│   ├── domain/{resource}.py           # Domain — 순수 엔티티, 비즈니스 규칙 (schema.md 매핑)
│   └── infrastructure/{resource}_repository.py  # Infrastructure — SQLAlchemy repo, Qdrant/Neo4j/MinIO/vLLM client
└── shared/                      # 모듈 간 공유 커널 (공통 예외·타입 — 도메인 엔티티 금지, F-2)
```

> 예: `modules/users/api/v1/users.py`, `modules/devices/domain/device.py`. 각 모듈은 자신의 4계층만 알고 다른 모듈의 `infrastructure/`를 직접 import하지 않는다(§6 의존 규칙과 동일 원칙을 모듈 경계에도 적용) — 이 경계가 지켜지면 향후 `modules/{module}/`을 통째로 별도 `services/{module}/`로 물리 분리해도 코드 이동만으로 끝난다.
>
> **Phase 1 구현 범위**: `users`·`devices` 모듈은 API/Application/Domain/Infrastructure 4계층 전부 참조 구현으로 완료. `sync` 모듈은 [sync-contract.md](../../02-design/sync-contract.md)의 엔드포인트 시그니처만 골격으로 구현(로직은 TODO). `author`·`care`·`schedule` 모듈은 도메인 엔티티만 정의하고 API/Application/Infrastructure는 후속 스프린트에서 구현한다.

---

## 3. 모바일 내부 구조 (Kotlin)

```
apps/mobile/src/main/java/com/silveryarn/mobile/
├── presentation/        # Jetpack Compose 화면 — 온보딩, 홈, 작가/말벗돌봄/비서 모드 UI
│   ├── onboarding/
│   ├── author/
│   ├── care/
│   ├── assistant/
│   └── settings/
├── ondevice/             # VAD·STT·SLM·TTS, 온디바이스 의도분류 라우터
│   ├── stt/
│   ├── slm/
│   └── tts/
├── local/                # Room(SQLite, FTS5 — Phase 1 기본 RAG, decisions.md #32)
│   ├── db/
│   └── vectorstore/       # 경량 VectorDB(임베딩) — 고사양 단말 한정 Phase 2+ 검토, Phase 1 미사용
├── installmode/          # 설치모드 자동분기 (Device Owner Mode 프로비저닝) — decisions.md #5,#6
└── sync/                 # Wi-Fi 배치 동기화 워커 (WorkManager)
```

---

## 4. 웹 콘솔 내부 구조 (Next.js, `apps/web`·`apps/admin` 공통 패턴) — v1.2 정정

> ⚠️ **정정 사유(2차 검증 M-7, CTO FE-B3)**: `presentation/app/`은 Next.js가 인식하지 못하는 경로라 라우팅이 동작하지 않는다. CONVENTIONS.md §3.2와 동일 구조로 통일했다.

```
apps/web/src/
├── app/                     # Next.js App Router 규약 위치 (라우트 그룹)
│   ├── (family)/              # 가족 대시보드, 원고 감수 등
│   └── (user)/                 # 자서전 사용자 화면
├── components/               # UI 컴포넌트
├── features/                 # 화면 단위 콜로케이션
├── services/                  # Application — API 서비스 래퍼
├── lib/api/                   # Infrastructure — 서버 API 클라이언트
└── types/                     # Domain — schema.md 엔티티와 1:1 매핑되는 TS 타입
```

계층 규율은 폴더 중첩이 아니라 ESLint `import/no-restricted-paths`로 강제한다(CONVENTIONS.md §3.2).

> `apps/admin`은 동일 패턴에 `(admin)/` 라우트 그룹만 다르게 구성 (사용자 관리, Wi-Fi 동기화 모니터링, 기기 관리 등 — UI/UX 화면설계서 "웹·관리자" 절 참조).

---

## 5. 화면 인벤토리 ↔ 폴더 매핑 (참고)

| UI/UX 화면설계서 화면 | 매핑 경로 |
|---|---|
| 온보딩·초기설정 (모바일) | `apps/mobile/.../presentation/onboarding/` |
| 자서전 작가모드 인터뷰 (모바일) | `apps/mobile/.../presentation/author/` |
| 자서전 뷰어·챕터 읽기 (웹) | `apps/web/.../app/(user)/chapters/` |
| 원고 감수·대조 편집 (웹·가족) | `apps/web/.../app/(family)/review/` |
| Wi-Fi 동기화 모니터링 (웹·관리자) | `apps/admin/.../app/(admin)/sync-monitor/` |
| 기기 관리 (웹·관리자, 신규) | `apps/admin/.../app/(admin)/devices/` |

---

## 6. Dependency Rules (모든 스택 공통)

> **v1.1 정정** (design-validator F-1): 아래 다이어그램과 표가 서로 다른 규칙을 말하던 문제를 해소 — "Application이 Infrastructure의 인터페이스(포트)에는 의존하되 구체 구현체를 직접 import하지 않는다"는 의존성 역전 원칙으로 통일했다.

```
Presentation ──→ Application ──→ Domain ←── Infrastructure

규칙: 안쪽 레이어는 바깥 레이어에 의존하지 않는다.
      Domain은 외부 의존성 없이 완전히 독립적이다 (순수 엔티티·규칙만).
      Infrastructure는 Domain이 정의한 인터페이스(Repository 등)를 구현하고,
      Application은 그 인터페이스를 통해서만 Infrastructure 기능을 사용한다
      (의존성 역전 — 구체 클래스가 아닌 Domain의 추상 인터페이스에 의존).
```

| From | Can Import | Cannot Import |
|------|-----------|----------------|
| Presentation | Application, Domain | Infrastructure 직접 |
| Application | Domain (항상), Infrastructure는 **Domain이 정의한 인터페이스 경유만** | Infrastructure 구체 구현 클래스 직접 import, Presentation |
| Domain | (없음, 독립) | 모든 외부 레이어 |
| Infrastructure | Domain만 (인터페이스 구현 목적) | Application, Presentation |

---

## Related Documents

- [CONVENTIONS.md](../../CONVENTIONS.md)
- [naming.md](./naming.md)
- Design §9 Clean Architecture: [silveryarn-platform.design.md](../02-design/features/silveryarn-platform.design.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-09-05 | Phase 2 초안 | NUBiz AX Initiative |
| 1.1 | 2026-09-05 | design-validator F-1(의존성 표 모순) 정정 | NUBiz AX Initiative |
| 1.2 | 2026-09-07 | 2차 design-validator 검증 반영 — Neo4j client 추가(§2), §4 웹 콘솔 App Router 경로 정정(M-7/FE-B3), "경량 VectorDB" 표현 정정(§3, M-8) | NUBiz AX Initiative |
| 1.3 | 2026-09-07 | 3차 design-validator 검증 반영 — M-6: `packages/py-common` 설명이 F-2 정정 취지와 충돌하던 것을 완화("공통 domain 엔티티"→"공통 유틸·인프라 헬퍼"). M-7(FE-B2): `packages/design-tokens/` 신규 추가(디자인 토큰 배포 메커니즘). L-6: §4 제목 버전 표기 정정("v1.1"→"v1.2") | NUBiz AX Initiative |
| 1.4 | 2026-09-07 | Do 단계 착수 — §1/§2를 `services/{engine}` 개별 마이크로서비스 제안에서 `services/backend/` 단일 배포 모듈러 모놀리스로 확정 반영(decisions.md #44, CTO Enterprise B3). 실제 스캐폴딩 코드와 동기화 | NUBiz AX Initiative |
