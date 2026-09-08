# Folder Structure Rules

> Phase 2 Deliverable — 모노레포 전체 구조 (Design 문서 §11.1을 실행 가능한 수준으로 구체화)

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-08 · **Version**: 1.11

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
│       │   ├── worker.py           # 비동기 잡 워커 진입점 (arq) — process_upload가 UploadPipelineService 실행
│       │   ├── core/                # config·db·logging·표준 에러 포맷(design.md §4.1)·auth·queue(arq pool)
│       │   │   └── clients/           # STT/Embedding/LLM(vLLM)/Qdrant/Neo4j 클라이언트 (횡단 관심사)
│       │   ├── modules/             # 도메인 모듈 — 상세는 §2. 8개 논리 모듈 전부 구현 완료
│       │   │   └── users/ devices/ author/ family_members/ invitations/ care/ schedule/ sync/ photos/
│       │   └── shared/              # 모듈 간 공유 커널 — domain_enums.py(공유 enum), schemas.py(공통 응답 포맷)
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
> **모듈 간 재사용**: 다른 모듈의 Application 서비스가 필요하면(예: `author`가 챕터 감수자 검증에 `family_members`를 씀) 그 모듈 루트의 `deps.py`(공개 조합 지점, FastAPI `Depends` 프로바이더)만 import한다. `family_members/deps.py`가 최초 사례 — 다른 모듈도 교차 참조가 생기면 동일 패턴을 따른다.
>
> **Phase 1 구현 범위**: `users`·`devices`·`author`(chapters/chapter_revisions)·`family_members`·`invitations`·`care`(conversation_chunks)·`schedule`(schedule_items)·`sync` 8개 논리 모듈은 4계층(또는 그에 준하는) 구현 완료. `photos`는 ORM 모델만 있는 골격(§2 실제 DB 검증 각주 참조) — 총 9개 모듈이 존재한다. `care`는 `conversation_chunks`만 구현했다 — `emotion_alerts`/`emotion_scores`는 Phase 1 피처플래그 OFF(decisions.md #25)라 의도적으로 제외했고, 검색은 실제 Qdrant 하이브리드 서치(design.md §2.4) 전까지 임시 DB ILIKE로 대체돼 있다(코드에 TODO 명시). `schedule`은 chapters/conversation_chunks와 달리 POST 생성을 공개로 노출한다 — AI 파이프라인 산출물이 아니라 가족·당사자가 직접 입력하는 리소스이기 때문이다.
>
> **sync 모듈의 파이프라인 오케스트레이션**: `SyncService`(접수+arq enqueue)와 `UploadPipelineService`(worker.py가 실행하는 실제 파이프라인 — STT 재전사→지식추출→임베딩/그래프 적재→챕터 갱신)로 분리했다. 각 외부 시스템 호출은 `core/clients/`(STT/Embedding/LLM/Qdrant/Neo4j, 횡단 관심사라 `core/`에 위치 — `core/db.py`와 동일 원칙)를 거치며, 실제 서비스가 없는 상태에서 REST 계약을 추정해 작성했다. 파이프라인은 각 단계를 best-effort로 감싸 부분 실패해도 계속 진행하고, `conversation_chunks` 적재 자체가 실패할 때만 `sync_sessions.status=failed`로 남긴다. `author`/`care`/`devices` 모듈에도 `deps.py`(공개 조합 지점)를 추가해 sync가 이들을 교차 참조할 수 있게 했다 — `family_members/deps.py`에서 시작한 패턴의 확장.
>
> **실제 커밋 버그 발견·수정**: `core/db.py`의 `get_db()`가 `session.commit()`을 호출하지 않아 — `flush()`만으로는 트랜잭션이 커밋되지 않으므로 — 지금까지 구현한 모든 쓰기 엔드포인트가 실제 Postgres에서는 아무것도 영속화하지 못하는 상태였다. 전부 페이크 Repository로 단위테스트해왔던 탓에 발견이 늦었다 — sync 파이프라인 구현 중 실제 트랜잭션 경계를 따라가다 확인하고 수정했다.
>
> **실제 DB/Redis/Qdrant/Neo4j를 붙인 엔드투엔드 검증(2026-09-08)에서 추가로 발견·수정한 버그 3건** — 전부 페이크 기반 단위테스트만으로는 드러나지 않았던 것들이다:
> 1. **ORM 모델 미등록으로 인한 FK 해석 실패**: `worker.py`가 자신이 직접 쓰는 Repository의 모델만 import해 `UserModel` 등이 Base.metadata에 등록되지 않았고, `conversation_chunks.user_id`(FK)를 flush하는 순간 `NoReferencedTableError`가 났다. `core/model_registry.py`를 신설해 모든 진입점(main.py/worker.py/migrations/env.py)이 이 파일 하나만 import하도록 통일 — 개별 import 목록의 중복 유지를 제거했다.
> 2. **photos 모듈 부재로 인한 동일 오류**: `conversation_chunks.linked_photo_id`가 schema.md DDL상 `REFERENCES photos(id)`인데 `photos`를 매핑하는 ORM 모델이 전혀 없어 같은 오류가 재발했다 — `photos` 모듈을 도메인 엔티티+ORM 모델만 있는 골격으로 신규 스캐폴딩해 해소(application/api는 다음 스프린트). `linked_chunk_id`(양방향 FK, erd.md §1 의도적 비정규화 2)는 ORM에 `ForeignKey`로 선언하지 않았다 — 순환 의존 복잡도를 피하기 위함(이 프로젝트는 ORM `relationship()`을 쓰지 않아 실익이 없음).
> 3. **세션 오염으로 실패 상태 기록이 2차 예외로 가려짐**: `conversation_chunks` flush 실패 후 같은(poisoned) 세션으로 `sync_sessions.status=failed`를 쓰려다 `PendingRollbackError`가 나 원래 원인이 로그에서 사라졌다. `UploadPipelineService`에서 상태 갱신 책임을 완전히 제거하고, `worker.py`가 **독립된 세션 + 즉시 커밋**으로 SUCCESS/FAILED를 기록하도록 재구성(`_update_sync_status()`).
> 4. **naive/aware datetime 비교 오류**: 모든 Repository가 `datetime.now()`(naive)로 타임스탬프를 만들었는데, Postgres `TIMESTAMPTZ` 컬럼은 asyncpg를 통해 항상 tz-aware로 돌아온다 — `invitations.ensure_acceptable()`가 만료 여부를 비교하다 `TypeError: can't compare offset-naive and offset-aware datetimes`로 실패했다. `src/` 전역(12개 파일)에서 `datetime.now()` → `datetime.now(UTC)`로 일괄 정정, 테스트 페이크도 동일하게 맞췄다.
>
> 이 4건 모두 `docker compose up` → `alembic upgrade head` → 실제 `uvicorn`+`arq` 프로세스로 HTTP 요청을 보내는 실제 엔드투엔드 검증 중에만 드러났다 — users/devices/family_members/invitations/schedule/chapters(review 포함)/sync 업로드 파이프라인 전체가 실제 Postgres·Redis·Neo4j·Qdrant에 대해 정상 동작함을 확인했다(Qdrant/LLM/STT/Embedding처럼 실제 서비스가 없는 것만 계획대로 best-effort 폴백).
>
> **author 모듈**: workflow-diagrams.md §4/§7의 M-5 정정(감수 전 chapter_revisions 생성 금지)을 코드 레벨에서 그대로 구현했다 — `save_draft()`(§4용, 이제 UploadPipelineService가 호출)와 `review_chapter()`(§7용, chapter_revisions 생성은 여기서만)를 분리.
>
> **family_members 모듈**: 다른 모듈(`author`의 `chapter_revisions.reviewer_id` 등)이 참조하는 루트 엔티티라 우선 구현했으며, 모듈 간 재사용은 `deps.py`라는 공개 조합 지점을 통해서만 하고 다른 모듈의 `infrastructure/`를 직접 import하지 않는 경계 규칙을 여기서 처음 적용했다(§2 의존 규칙의 모듈 간 확장).
>
> **invitations 모듈**: `family_members`의 임시 직접생성 경로(`POST /users/{userId}/family-members`)를 대체하는 정식 온보딩 경로다 — 수락(`POST /invitations/{token}/accept`) 시점에 `family_members/deps.py`를 통해 실제 family_member 행을 만들며, 두 모듈이 같은 FastAPI 요청의 `Depends(get_db)` 세션을 공유(요청별 캐싱)하므로 하나의 트랜잭션으로 묶인다. `family_role` enum처럼 2개 이상 모듈이 같은 Postgres enum을 참조하는 값 객체는 `core_service/shared/domain_enums.py`(공유 커널)에 두고 어느 한쪽 모듈의 domain/도 다른 모듈이 직접 import하지 않게 했다.

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
| 1.5 | 2026-09-07 | `author` 모듈(chapters/chapter_revisions) 4계층 구현 완료 반영 — §2 "Phase 1 구현 범위" 갱신 | NUBiz AX Initiative |
| 1.6 | 2026-09-07 | `family_members` 모듈 4계층 구현 완료 반영. 모듈 간 재사용 패턴(`deps.py` 공개 조합 지점) 신규 문서화 — §2 | NUBiz AX Initiative |
| 1.7 | 2026-09-08 | `invitations` 모듈 4계층 구현 완료 반영 — family_members 정식 온보딩 경로 완성. 2개 이상 모듈이 공유하는 enum은 `core_service/shared/domain_enums.py`(공유 커널)에 둔다는 원칙 신규 문서화 — §2 | NUBiz AX Initiative |
| 1.8 | 2026-09-08 | `care` 모듈(conversation_chunks) 4계층 구현 완료 반영 — emotion_alerts/emotion_scores는 Phase 1 피처플래그 OFF(decisions.md #25)로 의도적 제외, 검색은 임시 ILIKE(실제는 Qdrant 하이브리드 서치 예정)임을 명시 | NUBiz AX Initiative |
| 1.9 | 2026-09-08 | `schedule` 모듈(schedule_items) 4계층 구현 완료 반영 — 7개 논리 모듈(users/devices/author/family_members/invitations/care/schedule) 전부 구현 완료, `sync`만 골격 단계로 남음 | NUBiz AX Initiative |
| 1.10 | 2026-09-08 | `sync` 모듈 파이프라인 오케스트레이션 구현 반영(UploadPipelineService, core/clients/, core/queue.py) — 8개 논리 모듈 전부 구현 완료. `get_db()` 커밋 누락 버그 발견·수정 기록, `deps.py` 패턴을 author/care/devices로 확장 | NUBiz AX Initiative |
| 1.11 | 2026-09-08 | 실제 Postgres/Redis/Qdrant/Neo4j로 엔드투엔드 검증 — `photos` 모듈 신규 스캐폴딩(ORM 모델만, FK 해석 목적), `core/model_registry.py` 신설, `UploadPipelineService`/`worker.py` 세션 분리 재구성(`_update_sync_status`), 전역 naive datetime → `datetime.now(UTC)` 정정(12개 파일) 등 실제 인프라로만 드러나는 버그 4건 발견·수정 | NUBiz AX Initiative |
| 1.12 | 2026-09-08 | `apps/web` 스캐폴딩 완료 — §4 구조 그대로 구현(챕터 뷰어 `(user)/chapters`, 원고 감수 `(family)/review`), design.md §3.1 엔티티를 `types/`에 1:1 포팅, `lib/api`(케이스 변환·API 클라이언트)·`services`(Application) 계층 신설. **CORS 버그 발견·수정**: `services/backend`에 `CORSMiddleware`가 없어 Server Component fetch(Node 프로세스, CORS 미적용)는 통과하지만 "use client" 컴포넌트의 브라우저발 fetch만 조용히 `Failed to fetch`로 실패 — 실제 브라우저 자동화로 감수 승인 버튼을 눌러서만 드러난 버그. `core/config.py`에 `CORS_ALLOWED_ORIGINS` 설정 추가, `main.py`에 `CORSMiddleware` 등록으로 수정, 루트 `.env.example`에 반영. 부수적으로 실제 UI 클릭(반려 버튼) 검증 중 `(family)/review` 페이지가 반려(`rejected`) 상태 챕터를 목록 필터에서 빠뜨려(`draft`/`in_review`만 필터링) 반려 직후 화면에서 사라지는 버그도 발견·수정(`rejected` 포함하도록 필터 확장, schema.md #status v1.1 반영) | NUBiz AX Initiative |
| 1.13 | 2026-09-08 | `apps/admin` 스캐폴딩 완료 — §5 화면 인벤토리 그대로 구현(`devices/` 기기 관리, `sync-monitor/` Wi-Fi 동기화 모니터링). apps/web과 동일 계층·토큰을 공유 패키지 없이 각자 복사(`packages/design-tokens/` 추출은 후속 과제로 보류, 사유는 apps/admin/README.md). **관리자 조회 엔드포인트 신설**: 기존 `GET /sync/sessions/{id}`는 기기 자신의 폴링용(Device Token 인증)이라 관리자 콘솔이 그대로 쓰면 인가모델이 뒤섞인다 — 기존 엔드포인트는 그대로 두고 `GET /sync/sessions?device_id=...`(`require_auth`, `devices.py`의 `list_user_devices`와 동일한 "Admin — TODO: role 체크 강화" 패턴)를 신설, `SyncSessionRepository.list_by_device()`는 기존 `idx_sync_device` 인덱스를 그대로 활용. `SyncService` 유닛 테스트 신규(이전엔 전무했음). design.md §3.1도 함께 정정(Device.aiTops/lastSyncAt, SyncSession.startedAt/finishedAt — 코드에는 있었지만 문서에 누락, SoR 원칙 2 위반 시정) | NUBiz AX Initiative |
| 1.14 | 2026-09-08 | `GET /users` 전체 사용자 목록 엔드포인트 신규(`require_auth`, `?page=1&page_size=20`) — design.md §4.1이 문서화만 해 두고 어디서도 안 쓰이던 `PaginatedResponse`(`{ data, pagination }`) 봉투를 실제로 쓰는 첫 엔드포인트. `UserRepository.list_all()`은 `created_at DESC` 정렬(전용 인덱스는 아직 없음 — 사용자 수가 크지 않을 것으로 보고 보류). apps/admin 프론트엔드는 아직 이 엔드포인트를 소비하지 않음(화면은 후속 작업, apps/admin/README.md "아직 안 된 것" 참조) | NUBiz AX Initiative |
