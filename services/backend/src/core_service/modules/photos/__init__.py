"""photos 모듈 — 4계층 구현 완료(2026-09-08).

**왜 처음엔 ORM 모델만 있었나**: `care` 모듈의 `conversation_chunks.linked_photo_id`가
schema.md DDL상 `REFERENCES photos(id)`인데, `photos` 테이블을 매핑하는 ORM
모델이 어디에도 없어 — 실제 Postgres/Redis/arq로 엔드투엔드 검증하던 중 —
`conversation_chunks` insert가 전부 `NoReferencedTableError`로 실패하는 것을
발견했다. 그때는 FK 해석만 목적으로 ORM 모델만 급히 추가했다.

`linked_chunk_id`(photos → conversation_chunks)는 ORM에 FK로 선언하지 않았다 —
erd.md §1 "의도적 비정규화 2"(양방향 FK)가 실제 DB에는 있지만, 두 테이블을 서로
`ForeignKey(...)`로 선언하면 SQLAlchemy가 순환 의존으로 처리해야 해서 불필요한
복잡도가 생긴다. 이 프로젝트는 아직 ORM `relationship()`을 전혀 쓰지 않고
Repository로만 조회하므로, ORM 레벨 FK 선언은 실질적 이득이 없다 — 실제 무결성은
DB 제약(Alembic DDL)이 이미 보장한다.

**이번에 완성한 것**: sync-contract.md §4 Presigned URL 업로드 흐름 3단계
(`POST /photos/upload-url` → 클라이언트 MinIO 직접 PUT → `POST
/photos/{id}/complete`) + `GET /users/{userId}/photos` 목록 조회. `status`
컬럼(`pending_upload`/`uploaded`)을 schema.md v1.6로 신규 추가했다 — 문서가
이미 전제하던 흐름인데 §3.6 속성 표에는 빠져 있었다. `core/clients/storage_client.py`
(MinIO Presigned URL 클라이언트)도 신규 — STT/Embedding/LLM과 달리 이건 실제
로컬 docker-compose에 떠 있고 SDK 계약도 확정돼 있어 "추정 REST 계약"이 아니다.

**TODO(다음 스프린트)**:
- orphan cleanup 배치(sync-contract.md §4 — 24시간 지나도 `status=pending_upload`인
  행 정리)는 아직 없다. 지금은 `pending_upload`로 영구히 남을 수 있다.
- AI 자동 인라인 삽입 제안(`placement_status=proposed` → 챕터 본문 편입)은 author
  모듈이 담당할 몫으로 아직 미구현.
- `photo_requests`(가족→당사자 사진 추가 요청)는 완전히 별개 모듈로, 이번 범위에
  포함하지 않았다 — DB 테이블은 있지만 모듈 자체가 아직 스캐폴딩 전이다.
"""
