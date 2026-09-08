# services/backend — core-service

은빛실타래 서버의 첫 배포 단위. **모듈러 모놀리스**로 시작한다 — `api`(FastAPI)와 `worker`(비동기 잡) 2프로세스가 이 패키지의 코드를 공유하되 독립적으로 실행된다 (decisions.md #44, CTO Enterprise B3 "6개 마이크로서비스로 첫 커밋 금지" 반영).

## 왜 이런 구조인가

`docs/01-plan/structure.md §2`가 SoR이다. 요약하면:

- 도메인 모듈(`modules/{users,devices,author,care,schedule,sync,family_members,invitations}/`)은 각자 api/application/domain/infrastructure 4계층을 갖는다.
- 모듈은 서로의 `infrastructure/`를 직접 import하지 않는다 — 다른 모듈의 서비스가 필요하면 그 모듈의 `deps.py`(공개 조합 지점)만 거친다. 이 경계가 지켜지면 나중에 특정 모듈(예: GPU 부하가 큰 rag-core)만 별도 서비스로 분리할 때 코드 이동만으로 끝난다.
- 8개 논리 모듈(`users`/`devices`/`author`/`family_members`/`invitations`/`care`/`schedule`/`sync`) 전부 4계층 참조 구현 완료. `photos`는 ORM 모델만 있는 골격(FK 해석 목적, 아래 참조). `sync`의 STT/LLM/Embedding/Qdrant/Neo4j 클라이언트(`core/clients/`)는 실제 온프레미스 서비스가 아직 없어 **REST 계약을 추정해 작성**했다 — 인프라 배포 후 클라이언트 파일만 교체하면 되도록 인터페이스를 좁게 유지했다.
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

## 아직 안 된 것 (의도적 범위 제한)

- **온프레미스 AI 인프라 실물 연동 검증**: `core/clients/`(STT/Embedding/LLM)는 실제 서비스가 없는 상태에서 REST 계약을 추정해 작성했다 — 실 서비스 배포 후 계약이 다르면 이 파일들만 교체. Qdrant/Neo4j 클라이언트는 실제 컨테이너로 검증 완료(단, Qdrant는 embed 단계가 항상 실패해 실제로 upsert까지는 못 가봄 — EmbeddingClient 실 서비스 필요)
- **챕터 자동 귀속 재설계**: `UploadPipelineService`의 `PERIOD_TO_CHAPTER_NO`가 인생 시기 4개를 고정 챕터 번호에 매핑하는 최소 구현이다 — 같은 시기 내 다중 챕터 분화 미지원
- `sync` 모듈의 `GET /sync/download` — 여전히 빈 스냅샷 골격(chapter_updates 등 실제 조회 미구현)
- `photos` 모듈의 application/api 계층 — 지금은 ORM 모델만 존재(FK 해석 목적)
- PII 컬럼(schema.md §5) 암호화 — pgcrypto vs 애플리케이션 레벨 결정 대기
- Keycloak 실제 토큰 검증 — 현재 `core/auth.py`는 자리만 있고 미검증 스텁
- 오디오 업로드 자체(Presigned URL 또는 multipart) — `POST /sync/upload`가 지금은 `raw_audio_ref` 문자열을 클라이언트가 직접 주는 것으로 단순화돼 있음
