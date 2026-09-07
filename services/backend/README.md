# services/backend — core-service

은빛실타래 서버의 첫 배포 단위. **모듈러 모놀리스**로 시작한다 — `api`(FastAPI)와 `worker`(비동기 잡) 2프로세스가 이 패키지의 코드를 공유하되 독립적으로 실행된다 (decisions.md #44, CTO Enterprise B3 "6개 마이크로서비스로 첫 커밋 금지" 반영).

## 왜 이런 구조인가

`docs/01-plan/structure.md §2`가 SoR이다. 요약하면:

- 도메인 모듈(`modules/{users,devices,author,care,schedule,sync}/`)은 각자 api/application/domain/infrastructure 4계층을 갖는다.
- 모듈은 서로의 `infrastructure/`를 직접 import하지 않는다 — 이 경계가 지켜지면 나중에 특정 모듈(예: GPU 부하가 큰 rag-core)만 별도 서비스로 분리할 때 코드 이동만으로 끝난다.
- `users`·`devices`는 참조 구현(4계층 전부), `sync`는 API 골격만(sync-contract.md 시그니처), `author`/`care`/`schedule`은 도메인 엔티티만 정의된 상태다.

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

## 아직 안 된 것 (의도적 범위 제한)

- `author`/`care`/`schedule` 모듈의 API/Application/Infrastructure — 다음 스프린트
- `sync` 모듈의 실제 잡 처리 로직(전사·지식화·윤문 파이프라인) — Whisper/vLLM/Qdrant/Neo4j 연동 필요, 인프라 준비 후
- PII 컬럼(schema.md §5) 암호화 — pgcrypto vs 애플리케이션 레벨 결정 대기
- Keycloak 실제 토큰 검증 — 현재 `core/auth.py`는 자리만 있고 미검증 스텁
