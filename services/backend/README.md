# services/backend — core-service

은빛실타래 서버의 첫 배포 단위. **모듈러 모놀리스**로 시작한다 — `api`(FastAPI)와 `worker`(비동기 잡) 2프로세스가 이 패키지의 코드를 공유하되 독립적으로 실행된다 (decisions.md #44, CTO Enterprise B3 "6개 마이크로서비스로 첫 커밋 금지" 반영).

## 왜 이런 구조인가

`docs/01-plan/structure.md §2`가 SoR이다. 요약하면:

- 도메인 모듈(`modules/{users,devices,author,care,schedule,sync,family_members,invitations,photos,photo_requests}/`)은 각자 api/application/domain/infrastructure 4계층을 갖는다.
- 모듈은 서로의 `infrastructure/`를 직접 import하지 않는다 — 다른 모듈의 서비스가 필요하면 그 모듈의 `deps.py`(공개 조합 지점)만 거친다. 이 경계가 지켜지면 나중에 특정 모듈(예: GPU 부하가 큰 rag-core)만 별도 서비스로 분리할 때 코드 이동만으로 끝난다. `sync`의 `list_sessions` 라우터가 `devices/deps.py`(`get_device_service`)만 거쳐 기기 표시명을 조합하는 것, `photos`의 `complete_upload` 라우터가 `photo_requests/deps.py`(`get_photo_request_service`)만 거쳐 대기 중인 사진 요청을 자동 충족 처리하는 것이 이 원칙의 실제 사례다.
- 10개 논리 모듈(`users`/`devices`/`author`/`family_members`/`invitations`/`care`/`schedule`/`sync`/`photos`/`photo_requests`) 전부 4계층 참조 구현 완료(2026-09-08 `photo_requests` 완성으로 마지막 모듈 채움). `sync`의 STT/LLM/Embedding/Qdrant/Neo4j 클라이언트(`core/clients/`)는 실제 온프레미스 서비스가 아직 없어 **REST 계약을 추정해 작성**했다 — 인프라 배포 후 클라이언트 파일만 교체하면 되도록 인터페이스를 좁게 유지했다. `core/clients/storage_client.py`(MinIO)는 반대로 실제 서비스가 로컬에 떠 있고 SDK도 확정돼 있어 추정이 아니다.
- **모든 모듈 ORM 모델은 `core/model_registry.py` 하나만 import하면 등록된다** — 개별 진입점(main.py/worker.py/migrations/env.py)마다 모델 import 목록을 따로 유지하다 worker.py에서 실제로 하나(`UserModel`)를 빠뜨려 FK 해석 오류가 난 적이 있어(실제 DB 검증 중 발견) 이렇게 통일했다.

## 로컬 개발 준비

```bash
cd services/backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 인프라 기동 (Postgres/Redis/Qdrant/Neo4j/MinIO)
docker compose -f ../../infra/docker-compose.yml up -d

cp ../../.env.example ../../.env.local  # 값 채우기

alembic upgrade head        # schema.md DDL 전체 적용
uvicorn core_service.main:app --reload --port 8000   # api 프로세스
arq core_service.worker.WorkerSettings                # worker 프로세스 (별도 터미널)
```

## 검증

```bash
ruff check . && ruff format --check .
mypy src
pytest
```

### 실제 인프라 엔드투엔드 검증 완료 (2026-09-08)

`docker compose up` → `alembic upgrade head`(실 Postgres) → `uvicorn`+`arq`(실 Redis) 로 아래를 실제 HTTP 요청으로 확인했다:

- users/devices 생성 (decisions.md #5 설치모드 판별 포함, android_version 문자열 비교 버그 실사용 시나리오로 재확인)
- family_members 생성, invitations 생성→수락(family_members 자동 생성까지 하나의 트랜잭션)
- schedule_items 생성
- chapters 감수(review, reviewer_id 검증 포함) — chapter_revisions 정상 생성(M-5)
- sync/upload → arq 잡 → UploadPipelineService 전체 파이프라인 실행 → conversation_chunks 적재 → **실제 Neo4j에 그래프 노드 적재 확인**(Qdrant/STT/LLM은 실제 서비스가 없어 계획대로 best-effort 폴백)

이 과정에서 페이크 기반 단위테스트만으로는 드러나지 않던 버그 4건을 발견해 수정했다(`docs/01-plan/structure.md` §2 "실제 DB로 엔드투엔드 검증" 각주에 상세 기록) — ORM 모델 미등록으로 인한 FK 해석 실패, `photos` 모듈 부재, 세션 오염으로 인한 실패상태 기록 실패, naive/aware datetime 비교 오류.

### `photos` 모듈 완성 — 실제 MinIO Presigned URL 흐름 검증 (2026-09-08)

sync-contract.md §4 3단계 흐름을 실제 MinIO 컨테이너로 확인했다: `POST
/photos/upload-url`로 발급받은 서명 URL에 진짜 파일을 `curl -X PUT`으로 올리고
→ `mc ls`로 오브젝트가 정확한 키(`{user_id}/{photo_id}.jpg`)에 실제로 들어간 것
확인 → `POST /photos/{id}/complete` 호출 → `photos.status`가 `pending_upload`→
`uploaded`로 전이하는 것까지 DB에서 직접 확인. 멱등성(재호출해도 성공)·잘못된
`content_type`(400)·미인증(401)·Device Token으로도 통과되는지(200, either/or
인가)까지 curl로 검증.

### `photo_requests` 모듈 신규 — photos와의 자동 충족 연동까지 실제 검증 (2026-09-08)

DB 테이블은 첫 마이그레이션부터 있었지만 코드가 전혀 없던 마지막 모듈. `POST
/photo-requests`(생성) + `GET /users/{userId}/photo-requests`(목록, 스캐폴딩
시점 추가) + `POST /photo-requests/{id}/dismiss`(닫기, 스캐폴딩 시점 추가)를
구현하고, 충족(`fulfilled`)은 `photos`의 `POST /photos/{id}/complete`가
`photo_requests/deps.py`를 거쳐 자동 처리하도록 연결했다(schema.md §3.7
`fulfilled_at`이 이미 전제하던 흐름). 실제 요청을 만들고 → 실 MinIO에 사진을
올리고 → complete 콜백을 호출한 뒤 → 그 요청이 정말로 `fulfilled`로 바뀌는
것까지 curl로 확인했다(같은 사용자의 다른 pending 요청은 그대로 두는지, 이미
dismissed된 요청은 안 건드리는지도 함께).

### `GET /sync/download` 실제 구현 — 3개 모듈 조합, 실 DB로 증분 동작 검증 (2026-09-08)

빈 스냅샷 골격뿐이던 엔드포인트를 실제 조회로 채웠다. author(`chapters`)·
schedule(`schedule_items`)·신규 author(`questions` — schema.md §3.9 테이블은
있었으나 코드가 없던 갭, photo_requests와 같은 패턴으로 발견해 도메인/리포지토리/
서비스 채움) 3개 모듈을 sync 라우터가 각자의 `deps.py`로만 조합한다(구조 원칙
유지). `since` 워터마크 방식이 엔티티마다 다름을 실제 구현하며 확정: chapters는
`updated_at`, questions는 `updated_at` 컬럼이 없어 `created_at` 근사, schedule_items는
`updated_at`도 워터마크 컬럼도 없어 매번 "pending 전체"를 반환(자체로 멱등적
diff). 원문 계약엔 없던 `device_id` 필수 쿼리 파라미터를 추가로 발견해 넣었다
(Device Token이 아직 특정 기기를 검증 못 하는 스텁이라 호출 주체 식별 수단이
필요, sync-contract.md v0.3).

실 Postgres로 검증: 사용자·기기 생성(API) → 챕터/질문/일정 직접 INSERT(DB) →
`GET /sync/download`가 실제로 3개 항목을 다 돌려주는지 확인 → `since`를 이전
응답의 `sync_version`으로 다시 호출해 이미 받은 챕터/질문은 안 오고 새로 추가한
챕터만 오는지, 미응답 일정은 매번 다시 오는지까지 확인. `device_id` 누락(422)·
존재하지 않는 기기(404)·Device Token 없음(401) 에러 경로도 curl로 확인.

### `photos` orphan cleanup 배치 실제 구현 — 실 MinIO로 3가지 케이스 검증 (2026-09-08)

sync-contract.md §4가 명시한 "24시간 지나도 pending_upload면 정리"를 arq cron
job으로 구현했다(`worker.py`의 `cleanup_orphan_photos`, 매시 정각 실행 —
`WorkerSettings.cron_jobs`, API 요청 경로가 아니라 워커 프로세스 전용). MinIO
삭제(`StorageClient.remove_object`)는 대부분의 경우 객체가 애초에 없는 게
정상이라(presigned URL을 15분 안에 안 쓰면 그냥 방치되는 게 흔한 케이스)
`NoSuchKey`를 에러로 취급하지 않는다.

실 Postgres+MinIO로 3가지 케이스를 만들어 검증: (1) 24시간 넘게 지났고 실제로
MinIO에 파일까지 올라간 행 → DB 행과 MinIO 오브젝트 둘 다 삭제 확인(`mc ls`로
직접 확인), (2) 24시간 넘게 지났지만 파일은 결국 안 올라간 행(가장 흔한 케이스)
→ DB 행만 조용히 삭제(NoSuchKey 무시), (3) 아직 24시간 안 지난 최근 행 →
그대로 남아있음을 확인.

### PII 암호화·실 인증·동기화 멱등성·consent — 실 인프라 e2e (2026-09-09)

PR #1~#7 변경분을 실 Postgres + Keycloak으로 검증. `scripts/`에 재현 스크립트 3개:

| 스크립트 | 전제 | 검증 | 결과 |
|---|---|---|---|
| `e2e_pii_auth_check.py` | infra + `alembic upgrade head` | repository 계층: PII 암복호화·`contact_bidx` HMAC·`(session,turn)` 멱등성·crypto-shredding(`user_encryption_keys` 삭제→복호화 불가)·Device Token 해시 | **17/17** |
| `e2e_http_smoke.py` | + `uvicorn --port 9677` | HTTP: 부트스트랩 엔드포인트·Device Token 인가·IDOR 403·`access_logs` 미들웨어 적재 | **13/13** |
| `e2e_keycloak_check.py` | + `keycloak` 컨테이너 + `AUTH_ISSUER_URL` | 가족 토큰: JWKS RS256 검증·`sub`→`family_members` 매핑·`authorize_user_access` RBAC·social_worker fail-closed·2FA(`amr`) 게이팅·admin 전용 엔드포인트 | **9/9** |

이 과정에서 버그 1건 수정: 무인증 요청이 401 대신 500 (`require_verified_subject`가
토큰 검사 전에 `KeycloakVerifier`를 생성 — `AUTH_ISSUER_URL` 미설정 시 RuntimeError).

## 아직 안 된 것 (의도적 범위 제한)

- **온프레미스 AI 인프라 실물 연동 검증**: `core/clients/`(STT/Embedding/LLM)는 실제 서비스가 없는 상태에서 REST 계약을 추정해 작성했다 — 실 서비스 배포 후 계약이 다르면 이 파일들만 교체. Qdrant/Neo4j 클라이언트는 실제 컨테이너로 검증 완료(단, Qdrant는 embed 단계가 항상 실패해 실제로 upsert까지는 못 가봄 — EmbeddingClient 실 서비스 필요)
- **챕터 자동 귀속 재설계**: `UploadPipelineService`의 `PERIOD_TO_CHAPTER_NO`가 인생 시기 4개를 고정 챕터 번호에 매핑하는 최소 구현이다 — 같은 시기 내 다중 챕터 분화 미지원
- **Compaction Engine(design.md §2.11) 미구현** — `GET /sync/download`의 `chapter_updates.summary`가 AI 요약이 아니라 `body_text` 원문 그대로, `keywords`는 항상 빈 배열이다. 온디바이스 FTS5 검색은 되지만 "요약"은 아직 아니다 — 실 요약 파이프라인이 생기면 sync.py의 해당 자리만 교체
- 질문(`questions`) **자동 생성** 미구현 — author 모듈에 조회(`list_priority_questions_for_user`) 경로만 추가했다. 실제로 질문을 만드는 쪽(작가 엔진/온프레미스 LLM)은 아직 없어, 이 테이블에 아무도 안 넣으면 `priority_questions`는 계속 빈 배열
- AI 자동 인라인 사진 삽입 제안(`photos.placement_status=proposed` → 챕터 본문 편입) — author 모듈이 담당할 몫으로 아직 미구현
- `photo_requests`의 사진↔요청 1:1 매핑 — 두 테이블 사이에 연결 FK가 없어 "이 사용자가 사진을 올렸다"를 대기 중인 모든 요청에 대한 응답으로 해석해 일괄 충족 처리한다(정밀한 매핑이 필요해지면 photos에 fulfilled_request_id 같은 컬럼 추가 검토)
- ~~PII 컬럼 암호화~~ — 완료(1·2차, decisions.md #45, `core/crypto.py`). 3차(Vault 이전)만 남음
- ~~Keycloak 실제 토큰 검증~~ — 완료(decisions.md #47, `core/auth.py`). 로컬 realm은 `infra/keycloak/`. 온프레미스 realm 관리는 인프라 설계 과제
- `organizations` B2G 시설 테넌시 · retention 정책(`*.retention_until`) — 법무/운영모델 대기
- 오디오 업로드 자체(Presigned URL 또는 multipart) — `POST /sync/upload`가 지금은 `raw_audio_ref` 문자열을 클라이언트가 직접 주는 것으로 단순화돼 있음
