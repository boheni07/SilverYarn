# Folder Structure Rules

> Phase 2 Deliverable — 모노레포 전체 구조 (Design 문서 §11.1을 실행 가능한 수준으로 구체화)

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-08 · **Version**: 1.27

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
> **CI 강제(2026-09-10)**: 이 규칙들은 `services/backend/pyproject.toml`의 `[tool.importlinter]` contract로 강제된다(`ci.yml` backend job `lint-imports` 스텝) — ① 각 모듈 `api → application → infrastructure → domain` 역방향 import 금지, ② `domain`의 프레임워크(fastapi/sqlalchemy/pydantic) 의존 금지, ③ `core/`·`shared/`의 `modules/` 의존 금지(`core/model_registry`의 FK 해석용 ORM import만 예외). CTO Enterprise B3.
>
> **조립 지점(composition root)**: `main.py`·`worker.py`·`core/model_registry.py`·`core_service/auth_deps.py`는 여러 모듈을 자유롭게 조립하는 최상위 모듈이라 위 ③ 제약을 받지 않는다. 특히 `auth_deps.py`는 `core/auth.py`(순수 — 토큰 검증·인가 규칙·조회 포트 Protocol)를 `family_members`/`devices` 리포지토리와 엮는 FastAPI 의존성(`require_family`/`require_device`/`require_principal`/`require_roles`)을 두는 곳 — 라우터는 인증 심볼을 전부 여기서 가져온다.
>
> **모듈 간 재사용**: 다른 모듈의 Application 서비스가 필요하면(예: `author`가 챕터 감수자 검증에 `family_members`를 씀) 그 모듈 루트의 `deps.py`(공개 조합 지점, FastAPI `Depends` 프로바이더)만 import한다. `family_members/deps.py`가 최초 사례 — 다른 모듈도 교차 참조가 생기면 동일 패턴을 따른다.
>
> **Phase 1 구현 범위**: `users`·`devices`·`author`(chapters/chapter_revisions)·`family_members`·`invitations`·`care`(conversation_chunks)·`schedule`(schedule_items)·`sync`·`photos`(업로드 URL 발급/완료 확인/목록)·`photo_requests`(가족 요청 생성/목록/닫기, 충족은 photos 모듈이 자동 처리) 10개 논리 모듈 전부 4계층(또는 그에 준하는) 구현 완료. `care`는 `conversation_chunks`만 구현했다 — `emotion_alerts`/`emotion_scores`는 Phase 1 피처플래그 OFF(decisions.md #25)라 의도적으로 제외했고, 검색은 실제 Qdrant 하이브리드 서치(design.md §2.4) 전까지 임시 DB ILIKE로 대체돼 있다(코드에 TODO 명시). `schedule`은 chapters/conversation_chunks와 달리 POST 생성을 공개로 노출한다 — AI 파이프라인 산출물이 아니라 가족·당사자가 직접 입력하는 리소스이기 때문이다. `photos`의 orphan cleanup 배치(sync-contract.md §4, 24시간 지나도 `pending_upload`인 행 정리)는 아직 미구현이다.
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
| 사용자 관리 (웹·관리자, 신규 v1.15) | `apps/admin/.../app/(admin)/users/` — apps/admin의 실질적 진입점(홈 1차 CTA) |

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
| 1.15 | 2026-09-08 | `apps/admin` `(admin)/users` 사용자 목록 화면 신규 — `GET /users`를 실제로 소비하는 첫 화면이자 apps/admin의 실질적 진입점(홈 1차 CTA, 기존 ID 직접입력 폼은 보조 수단으로 하향). `{ data, pagination }` 봉투 전체가 필요해 `lib/api/client.ts`에 `apiClient.getPaginated()` 신규(기존 `get()`은 `pagination`을 버렸음). design.md §3.1 User에 `createdAt`/`updatedAt` 보강(Device/SyncSession과 동일한 SoR 시정 패턴) — §5 화면 인벤토리 표에 `users/` 행 추가 | NUBiz AX Initiative |
| 1.16 | 2026-09-08 | `apps/admin` "전체 기기 통합 모니터링" — `(admin)/sync-monitor`가 `deviceId` URL 파라미터 유무로 기기별/전체 두 모드를 겸하도록 확장(상태 필터·페이지네이션 추가). 백엔드 `GET /sync/sessions`의 `device_id`를 필수→선택으로 바꾸고 `status`·페이지네이션 파라미터 추가, `SyncSessionRepository`의 `list_by_device()`/`list_all()`을 하나로 통합. 새 `idx_sync_started_at` 인덱스 추가(schema.md v1.5) — `migrations/versions/0001_initial_schema.py`에 반영 + 이미 적용된 로컬 DB에는 `CREATE INDEX` 직접 실행으로 맞춤 | NUBiz AX Initiative |
| 1.17 | 2026-09-08 | `GET /sync/sessions` 응답에 기기 표시명(`deviceDisplayId`) 추가 — `devices` 모듈에 `DeviceRepository.list_by_ids()`(IN 쿼리)·`DeviceService.get_display_ids()` 신규, `sync` 라우터가 `devices/deps.py`(`get_device_service`, upload 엔드포인트가 이미 쓰던 것)로만 호출해 조합. `sync` 모듈이 `devices` 테이블을 직접 조인하지 않는다는 모듈 경계 원칙(§2) 유지. `tests/modules/devices/test_device_service.py` 신규(3 테스트) | NUBiz AX Initiative |
| 1.18 | 2026-09-08 | `GET /users`에 이름 검색(`name`, ILIKE 부분일치) 추가, `apps/admin` `(admin)/users`에 검색창 신설 — 자바스크립트 없이 동작하는 순수 `<form method="GET">`(검색은 새 URL 이동이라 클라이언트 상태 불필요). 검색어를 유지한 채 페이지네이션. `tests/modules/users/test_user_service.py`에 검색 테스트 4건 추가 | NUBiz AX Initiative |
| 1.19 | 2026-09-08 | `.github/workflows/ci.yml` 신규 — 이 세션 내내 사람이 수동으로 돌려 온 검증(`ruff check`/`ruff format --check`/`mypy`/`pytest` for services/backend, `npm run lint`/`type-check`/`build` for apps/web·apps/admin)을 push/PR마다 자동 실행. backend job은 실 인프라 없이 Fake*Repository 기반 Application 계층 테스트만 돈다(실 DB e2e 검증은 여전히 로컬 docker-compose로 사람이 수행). `apps/mobile`은 스캐폴딩 전이라 job 없음. 커밋 전 3개 job 전부(mypy 최초 실행 포함, 113개 소스 파일 이상 없음 확인) 로컬로 재현해 통과 확인 | NUBiz AX Initiative |
| 1.20 | 2026-09-08 | `photos` 모듈 완성(ORM 모델만 있던 골격 → application/api 4계층) — 9개 논리 모듈 전부 구현 완료. sync-contract.md §4 Presigned URL 3단계 흐름(`POST /photos/upload-url` → 클라이언트 MinIO 직접 PUT → `POST /photos/{id}/complete`) + `GET /users/{userId}/photos` 신규. `photos.status`(`pending_upload`/`uploaded`) 컬럼 신규(schema.md v1.6) — sync-contract.md가 이미 전제하던 흐름인데 §3.6 속성 표엔 빠져 있던 걸 발견. `core/clients/storage_client.py`(MinIO Presigned URL, 실제 SDK 확정이라 STT/Embedding/LLM과 달리 "추정 계약" 아님) 신규. "2FA + Role(family) 또는 Device Token" 인가를 위한 `require_auth_or_device_token` 복합 의존성 신규(core/auth.py) — 이 프로젝트 첫 either/or 인가 패턴. sync-contract.md §4 예시 요청 본문에 `user_id`/`uploader_type` 누락돼 있던 걸 발견·보강(v0.2). 실 MinIO에 진짜 파일 PUT → presigned URL 서명 검증 → complete 콜백까지 curl로 e2e 확인 | NUBiz AX Initiative |
| 1.21 | 2026-09-08 | `photo_requests` 모듈 신규 스캐폴딩(도메인부터 4계층 전부, DB 테이블은 0001 마이그레이션에 이미 있었으나 코드가 아예 없었음) — 10개 논리 모듈 전부 구현 완료. design.md §4.2에 `GET /users/{userId}/photo-requests`·`POST /photo-requests/{id}/dismiss` 신규(§4.2 v0.13, invitations 모듈과 동일 사유로 스캐폴딩 시점 추가). `photos`의 `POST /photos/{id}/complete`가 `photo_requests/deps.py`(신규, `get_photo_request_service`)를 거쳐 대기 중인 사진 요청을 자동으로 fulfilled 처리 — schema.md §3.7 `fulfilled_at`이 이미 전제하던 흐름을 실제로 연결. 어느 사진이 어느 요청에 대한 응답인지 연결하는 FK가 스키마에 없어 "이 사용자가 사진을 올렸다"를 대기 중인 모든 요청에 대한 응답으로 해석(1:1 매핑 아님, 코드 주석에 명시). 실 API로 생성→목록조회→실 MinIO 업로드→complete→자동 fulfilled 전이까지 curl로 e2e 확인 | NUBiz AX Initiative |
| 1.22 | 2026-09-08 | `apps/mobile` 스캐폴딩 착수 — §3(모바일 내부 구조)·CONVENTIONS.md §2 그대로 5개 패키지(`presentation/`·`ondevice/`·`local/`·`installmode/`·`sync/`) 생성. `local/db/`는 mobile-schema.md 6개 테이블 전부 구현(5개 Room `@Entity`, `autobiography_fts`는 FTS5라 `AutobiographyFtsStore`가 raw SQL로 접근 — Room `@Dao`로 만들면 KSP가 "no such table" 컴파일 에러를 낸다는 걸 리뷰 중 발견해 정정). `installmode/InstallModeResolver`는 decisions.md #5 임계값을 services/backend `determine_install_mode()`와 동일하게 이식 + JUnit 테스트(services/backend test_install_mode.py와 동일 경계값). `sync/SyncApi`는 services/backend 실 엔드포인트(POST /devices, POST /sync/upload, GET /sync/sessions/{id}, GET /sync/download)와 1:1 매핑. **⚠️ 이 세션 환경에 JDK/Android SDK/Gradle이 없어(`java -version`/`gradle -v` 직접 확인) ktlintCheck/test/assembleDebug를 전혀 실행하지 못했다** — 다른 모든 모듈과 달리 컴파일조차 검증 안 된 상태(apps/mobile/README.md "환경 제약" 참조), 대신 코드 리뷰만으로 Moshi codegen 의존성 누락·TTS 초기화 순서 버그·Room-FTS5 컴파일 에러를 발견해 수정. `mobile-schema.md`에 `device_state.device_id` 컬럼 신규(v0.4) — 등록 이후 동기화 호출이 자기 device_id를 저장할 곳이 없던 걸 발견 | NUBiz AX Initiative |
| 1.27 | 2026-09-08 | apps/web `(family)/photo-requests` 사진 요청 화면 신규 — photo_requests API(생성/조회/닫기)는 이미 완성돼 있었으나 소비하는 화면이 web·admin 어디에도 없던 갭을 메웠다. `PhotoRequestForm`(가족이 요청 생성)·`PendingPhotoRequestBanner`(당사자가 `(user)/photos` 상단에서 대기 요청을 보고 닫기) 신규 — 충족(fulfilled)은 사진 업로드 시 서버가 자동 처리하므로 두 화면 다 별도 "충족" 버튼 없음. `Photo`/`PhotoRequest` 타입에 누락 필드(createdAt/fulfilledAt 등) 보강. 실 백엔드+`next dev`+claude-in-chrome으로 요청 생성→배너 노출→닫기→Postgres 상태 전이까지 확인 | NUBiz AX Initiative |
| 1.26 | 2026-09-08 | apps/web `(user)/photos` 사진 갤러리 화면 신규 — design.md §5.1 화면 인벤토리의 "사진·타임라인 갤러리" 최초 구현이자 sync-contract.md §4 Presigned URL 흐름을 소비하는 첫 웹 화면(`PhotoUploadForm` client component: upload-url 발급 → 브라우저가 MinIO에 직접 PUT → complete 콜백). 사진을 "보여주는" 문제를 새로 풀었다 — `storage_ref`는 내부 MinIO 키라 브라우저가 못 열어, `GET /users/{userId}/photos`에 `view_url`(presigned GET URL, uploaded 상태에서만 존재) 신규(`PhotoService.get_view_url`, `StorageClient.presigned_get_url`). apps/web `Photo` 타입(design.md §3.1)에 `status`(schema.md v1.6엔 있었으나 누락돼 있던 것 발견)·`viewUrl` 보강. 백엔드 유닛테스트 2건 추가(105개), 실 uvicorn+MinIO+`next dev`+claude-in-chrome으로 실제 파일 업로드→갤러리 렌더링→DB 상태 전이까지 확인, 지원 안 하는 파일 형식의 클라이언트 측 검증도 확인 | NUBiz AX Initiative |
| 1.25 | 2026-09-08 | `photos` orphan cleanup 배치 실제 구현 — sync-contract.md §4가 명시했던 "24시간 지나도 pending_upload면 정리"를 arq cron job으로 채움(`worker.py`의 `cleanup_orphan_photos`, 매시 정각, `WorkerSettings.cron_jobs`). `PhotoRepository`에 `list_pending_upload_older_than()`·`delete()`, `PhotoService`에 `cleanup_orphan_pending_uploads()`, `StorageClient`에 `remove_object()`(NoSuchKey는 정상 케이스로 무시) 신규. 실 Postgres+MinIO로 3가지 케이스(오브젝트 있는 채로 방치/오브젝트 없이 방치/최근 생성) 검증 — 유닛테스트 3건 추가(103개) | NUBiz AX Initiative |
| 1.24 | 2026-09-08 | `GET /sync/download` 실제 구현 — backend↔mobile 동기화 루프가 처음으로 끝까지 이어짐. **backend**: author 모듈에 `questions` 도메인/리포지토리/서비스 신규(schema.md §3.9 테이블은 있었으나 코드가 없던 갭), schedule 모듈에 `deps.py` 신규, sync 라우터가 이 둘 + author의 chapters를 각자 deps.py로만 조합. 원문 계약에 없던 `device_id` 필수 쿼리 파라미터 신규 발견(sync-contract.md v0.3, Device Token 스텁이라 호출 주체 식별 수단 필요). 엔티티별 워터마크 방식이 실제로 다름을 확정(chapters=updated_at, questions=created_at 근사, schedule_items=pending 상태 전체). chapter_updates의 summary/keywords는 §2.11 Compaction Engine 미구현으로 body_text 원문/빈 배열 대체. 실 Postgres로 증분 동작(since 재호출 시 이미 받은 것 제외) 검증. **mobile**: `SyncWorker`가 실제로 download()를 호출해 3개 로컬 캐시(FTS5/questions_cache/schedule_cache)에 반영하도록 구현 — `device_state.last_sync_version` 컬럼 신규(mobile-schema.md v0.5, 서버 발급 `sync_version` 커서를 그대로 왕복시킬 저장소가 없던 두 번째 갭). IntelliJ 번들 JBR + ktlint CLI로 로컬 재검증 후 CI 확인 | NUBiz AX Initiative |
| 1.30 | 2026-09-10 | 챕터 Compaction Engine(design §2.11 4단계) 부분 구현 — `core/clients/llm_client.py`에 `compact_chapter` 신규(vLLM), `author` 도메인에 `ChapterCompaction` + `Chapter.compaction_is_stale`, `ChapterService.compact_chapter`(stale 판정), 업로드 파이프라인이 `save_draft` 직후 best-effort 호출. `chapters`에 `compaction_summary`/`compaction_keywords`/`compacted_version` 3컬럼(마이그레이션 `0007`). `GET /sync/download`가 `body_text` 원문 대신 요약(없으면 앞 200자)을 내려보냄. 유닛테스트 5건 추가(150개), 마이그레이션 up/down/up + PII e2e 17/17 재확인 | NUBiz AX Initiative |
| 1.29 | 2026-09-10 | `core/auth.py` 순수화 — import-linter contract ③의 예외였던 auth→모듈 infrastructure 결합 2건 제거. `core/auth.py`는 순수(토큰 검증·인가 규칙·조회 포트 `FamilyMemberDirectory`/`DeviceTokenDirectory` Protocol), 리포지토리 조립 FastAPI 의존성은 `core_service/auth_deps.py`(신규 composition root)로 이동. 13개 라우터가 `auth_deps`에서 인증 심볼 import. §2에 composition root 개념 추가 | NUBiz AX Initiative |
| 1.28 | 2026-09-10 | §2에 모듈 경계·4계층 규칙의 **CI 강제** 명시 — `services/backend/pyproject.toml [tool.importlinter]` contract 4개(모듈 layers, domain 프레임워크 의존 금지, `shared/`·`core/`의 `modules/` 의존 금지) + `ci.yml` backend job `lint-imports` 스텝. PDCA Check(gap-analysis G2) 후속. 도입 중 `modules/photo_requests/__init__.py` 누락 발견·수정(암묵적 namespace 패키지라 grimp가 인식 못 하던 결함, G6). `core/auth.py`가 principal 해석에 `family_members`/`devices` 리포지토리를 지연 import하는 2건은 예외로 고정(core에 포트 두고 주입하는 리팩터링이 후속) | NUBiz AX Initiative |
| 1.23 | 2026-09-08 | `apps/mobile` CI(`mobile` job) 최초 그린 — 1.22가 남긴 "컴파일조차 검증 안 된 상태"가 해소됐다. 이 세션 로컬 환경엔 여전히 Android SDK가 없지만, IntelliJ IDEA 번들 JBR(JDK 21)로 ktlint CLI(1.3.1/1.8.0)를 직접 돌려 실제 파싱·포맷 검증을 먼저 해보고 나서 푸시하는 방식으로 CI 왕복을 줄였다. 3회 CI 실행에서 실제 버그 3건 발견·수정: (1) `sync/SyncApi.kt` KDoc 안 문자열 "api/v1/*.py"의 "/*"가 Kotlin 블록 주석의 중첩(nest) 규칙과 충돌해 파일 끝까지 주석이 안 닫힘("KtLint failed to parse file") — 표현 변경으로 "/*" 시퀀스 제거. (2) 여러 파일의 생성자 파라미터/함수 인자 목록 안 trailing `//` 주석이 ktlint 규칙 위반(자동수정 불가) — 전부 파라미터 앞 독립 줄로 이동. (3) `ic_launcher_background.xml` XML 주석 안의 리터럴 "--"(CSS 커스텀 프로퍼티 표기를 그대로 옮겨 적은 것)가 XML 스펙 위반으로 `mergeDebugResources` 리소스 컴파일 실패 — "--" 제거. 그 외 순수 포맷팅 위반 다수(`ktlint -F`로 자동 수정) + `.editorconfig`에 `ktlint_function_naming_ignore_when_annotated_with = Composable` 추가(Jetpack Compose PascalCase 컨벤션과 ktlint 기본 lowerCamelCase 룰 충돌 해소, ktlint 공식 지원 옵션). 지금은 `ktlint`/`test`/`assembleDebug` 3단계 전부 CI 그린 — Room/Moshi/KSP codegen과 Compose 컴파일, APK 어셈블까지 실제로 검증됨(apps/mobile/README.md "환경 제약" 갱신) | NUBiz AX Initiative |
