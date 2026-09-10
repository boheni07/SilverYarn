# PDCA Check — 설계문서 ↔ 구현 갭 분석

> **Date**: 2026-09-10
> **범위**: `docs/02-design/features/silveryarn-platform.design.md` v0.26 · `docs/01-plan/schema.md` v1.11 · `docs/02-design/sync-contract.md` v0.5 · `docs/01-plan/structure.md` v1.x ↔ `services/backend/src/core_service/` 실 구현, 실 DB(마이그레이션 0006), `apps/mobile`
> **방법**: 수동 대조 (엔드포인트 목록, ORM `__tablename__`/컬럼, 모듈 간 import 그래프, 4계층 의존, 실 DB `information_schema` 덤프)
> **선행**: Do 단계 보안 트랙 PR #1~8 머지 완료, 실 인프라 e2e 3종(pii 17/17 · http 13/13 · keycloak 9/9) green

---

## 요약

| # | 구분 | 항목 | 조치 |
|---|---|---|---|
| G1 | 문서 드리프트 | design §9.1/§11.1이 미구현 `services/{engine}/` 6-서비스 구조로 서술 | design v0.27에서 실제 구조로 교체 ✅ |
| G2 | 강제 부재 | 모듈 경계 CI 강제(import-linter) 미도입 — CTO Enterprise B3 권고 | **import-linter 4개 contract 도입 + CI 배선 완료** (`chore/import-linter-module-boundaries`, pyproject.toml `[tool.importlinter]`, ci.yml backend job) ✅ |
| G3 | 문서 드리프트 | design §3.1 `interface Chapter.createdAt` — 테이블·ORM·응답·DDL 어디에도 없음 | design v0.27에서 제거 ✅ |
| G4 | 문서 내부 불일치 | §8.1 Test Plan이 정서 모니터링·출판을 "Phase Do"로 표기 (§11.2·decisions #25와 모순) | design v0.27에서 Phase 2/3로 정정 ✅ |
| G5 | 의도된 이연(확인) | `emotion-scores`/`emotion-alerts`/`publications` 엔드포인트 미구현 | 정상 — Phase 2/3, 피처플래그 OFF. 문서에 이연 근거 존재 |
| G6 | 구현 결함 | `modules/photo_requests/__init__.py` 누락 — 나머지 11개 모듈엔 모두 존재. 암묵적 namespace 패키지라 런타임 import는 되지만 정적 도구(grimp/import-linter)가 패키지를 못 봄 | `__init__.py` 추가 (import-linter 도입 중 발견) ✅ |

정상 확인: schema.md §5 DDL ↔ 실 DB 21개 테이블 컬럼 일치. 4계층 의존 규칙(domain 순수·역참조 0)·모듈 경계(타 모듈 `infrastructure`/`api` 직접 import 0건) 준수. 마이그레이션 0001~0006 전부 적용.

---

## G1. 설계문서 구조 서술 ↔ 실제 구현 불일치

**설계문서(v0.26 §9.1, §11.1)**: 서버를 `services/{gateway,author-engine,care-engine,schedule-engine,sync-gateway,rag-core,shared}/` 6개 서비스 + `packages/py-common/`로 서술.

**실제 구현**: 단일 모듈러 모놀리스.

```
services/backend/src/core_service/
├── main.py          # api 프로세스 (FastAPI)
├── worker.py        # worker 프로세스 (arq)
├── core/            # 횡단: auth, crypto, db, queue, config, model_registry, access_log
│   └── clients/
├── shared/          # 공유 커널 (domain_enums.py — 2+ 모듈이 쓰는 enum)
└── modules/{users,devices,author,care,schedule,sync,consent,
          family_members,invitations,notifications,photos,photo_requests}/
    ├── api/v1/  application/  domain/  infrastructure/  deps.py
```

- `decisions.md #44`가 이 전환을 확정했고 `structure.md` v1.4가 이미 반영. **design 문서만 뒤처져 있었음.**
- `packages/py-common`·`services/{gateway,*-engine,rag-core,shared}`는 생성되지 않음.

**조치**: design v0.27 §9.1 Location 열·§11.1 트리를 실제 구조로 교체. SoR 원칙 1(코드 우선).

---

## G2. 모듈 경계 CI 강제 부재 (CTO Enterprise B3)

**권고(design §11 preamble)**: "폴더 경계만 유지하며 **import-linter로 엔진 간 직접 참조를 CI에서 차단**".

**발견 당시 현황**:
- `services/backend/pyproject.toml`에 `[tool.importlinter]` 없음, `.github/workflows/ci.yml`에 contract 검사 스텝 없음.
- **현재 코드는 경계를 지키고 있었음**:
  - 모듈 간 교차 import는 `application`(서비스 클래스)·`domain`(값 객체·enum)·`deps`(DI 제공자)로 한정. 타 모듈 `infrastructure`/`api` 직접 import **0건**.
  - 실제 교차 지점: `author→family_members`, `consent→family_members`, `invitations→family_members`, `photos→photo_requests`, `photo_requests→family_members`, `sync→{author,devices,schedule}`, `sync(upload_pipeline)→{author,care}` — 전부 `.application`/`.domain`/`.deps`.
  - 4계층: `domain/*.py`는 `fastapi`/`sqlalchemy`/상위 계층 import 0. `application`→`api` 역참조 0. `infrastructure`→`application`/`api` 역참조 0.
  - 예외: `core/auth.py`가 principal 해석에 `family_members`/`devices`의 infrastructure를 함수 내부 지연 import(정석은 core에 포트를 두고 주입 — 후속 리팩터링).

**조치 (완료)**: `import-linter>=2.0` 추가, `pyproject.toml [tool.importlinter]`에 contract 4개:
1. **layers** — 12개 도메인 모듈 각각 `api → application → infrastructure → domain` (역방향 import 금지)
2. **forbidden** — `modules.*.domain`은 `fastapi`/`sqlalchemy`/`pydantic`에 의존 금지 (순수성)
3. **forbidden** — `core_service.shared`는 `core_service.modules`에 의존 금지
4. **forbidden** — `core_service.core`는 `core_service.modules`에 의존 금지 (예외 3건 `ignore_imports`로 고정: `model_registry`의 ORM 전체 import + `auth.py`의 2건)

CI: `ci.yml` backend job에 `lint-imports` 스텝(mypy 다음). 로컬: `4 kept, 0 broken` 확인.

---

## G3. design §3.1 `interface Chapter.createdAt` — 존재하지 않는 필드

- design v0.6 L-11(design-validator)에서 `Chapter.createdAt`/`updatedAt` 추가.
- 그러나 `chapters` 테이블(0001 DDL)·`ChapterModel`·`Chapter` 도메인·`ChapterResponse` 모두 **`updated_at`만 존재**. `schema.md` §5 DDL에도 `created_at` 없음.
- `updated_at`이 이미 `GET /sync/download` 증분 워터마크로 기능(`chapter_repository.list_updated_since`). `created_at` 소비처 없음.

**조치**: design v0.27 §3.1 `interface Chapter`에서 `createdAt` 제거(코드 우선). 필요해지면 마이그레이션으로 컬럼 추가 후 되살린다.

---

## G4. Test Plan(§8.1) ↔ Implementation Order(§11.2) phase 불일치

- §8.1은 "정서 모니터링", "출판 파이프라인" 행의 Phase를 **Do**로 표기.
- §11.2는 정서 모니터링 = step 6 (Phase 2), 출판 = step 7 (Phase 3).
- `decisions.md #25`: 정서 모니터링 파이프라인은 Phase 1에서 **피처플래그 OFF**.
- design §7.4: "미적용(후속): `emotion_alerts`/`emotion_scores` 엔드포인트(피처플래그 OFF)".

**조치**: design v0.27 §8.1 Phase 열을 `Phase 2 (피처플래그 OFF)` / `Phase 3`으로 정정.

---

## G5. 미구현 엔드포인트 3종 — 의도된 이연 (gap 아님, 확인 기록)

design §4.2 Endpoint List에 있으나 미구현:

| 엔드포인트 | 상태 | 근거 |
|---|---|---|
| `GET /api/v1/users/{userId}/emotion-scores` | 미구현 | Phase 2, 피처플래그 OFF (decisions #25, design §7.4). `emotion_scores` 테이블은 0001에 존재 |
| `GET /api/v1/users/{userId}/emotion-alerts` | 미구현 | 동상 |
| `POST /api/v1/users/{userId}/publications` | 미구현 | Phase 3 (§11.2 step 7). `publications` 테이블·enum(`publication_format`/`publication_status`) 0001에 존재. 도메인 모듈 없음 |

이연이 정상이나, 3개 테이블이 마이그레이션에 살아 있고 엔드포인트 표에도 남아 있어 "잊힌 것"과 구분이 안 됨 → design §8.1/§11.2에 phase를 못박아 해소(G4).

---

## 정상 확인 항목

| 항목 | 결과 |
|---|---|
| schema.md §5 DDL ↔ 실 DB 컬럼 | 일치 (spot-check: users, family_members, devices, chapters, chapter_revisions, conversation_chunks, photos, photo_requests, questions, schedule_items) |
| 마이그레이션 | 0001~0006 전부 적용 (`alembic_version = 0006`) |
| 실 인프라 e2e | `e2e_pii_auth_check.py` 17/17 · `e2e_http_smoke.py` 13/13 · `e2e_keycloak_check.py` 9/9 |
| 4계층 의존 규칙 | domain 순수(외부·상위 계층 import 0), application→api 역참조 0, infrastructure→application/api 역참조 0 |
| 모듈 경계 | 타 모듈 `infrastructure`/`api` 직접 import 0건 (전부 `application`/`domain`/`deps` 경유) |
| `receives_emotion_alerts` 기본값 | `false` (CTO B1 opt-out — 마이그레이션 0005) |
| `notification_settings (family_member_id, channel)` UNIQUE | 적용됨 (0005) |
| `uq_conversation_chunks_turn` 부분 유니크 인덱스 | 적용됨 (0004, sync 멱등성 3계층) |

---

## 후속 (별도 트랙)

1. ~~import-linter 도입 (G2)~~ — **완료** (`chore/import-linter-module-boundaries`).
2. **모바일 앱 흐름 완성** — 온보딩 재시작 스킵(`device_state.device_id`), install_mode 기반 진입 분기(키오스크 lockTask), 최초 동기화 화면: **완료** (`feat/mobile-app-entry-first-sync`). 가족 초대 수락 화면은 첫 가족 연결 경로 설계 결정 대기라 제외.
3. **`core/auth.py` → 모듈 infrastructure 결합 제거** — core에 리포지토리 포트(Protocol) 정의 후 주입. 현재 import-linter contract 4에 예외 2건으로 고정돼 있음.
4. ~~PDCA Report 생성~~ — **완료** (`docs/04-report/features/silveryarn-platform.report.md`, PR #1~11 + Check 종합).
