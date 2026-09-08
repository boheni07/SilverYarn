"""photos 모듈 — 도메인 엔티티 + ORM 모델만 존재하는 골격 상태.

⚠️ **왜 갑자기 필요해졌나**: `care` 모듈의 `conversation_chunks.linked_photo_id`가
schema.md DDL상 `REFERENCES photos(id)`인데, `photos` 테이블을 매핑하는 ORM
모델이 어디에도 없어 — 실제 Postgres/Redis/arq로 엔드투엔드 검증하던 중 —
`conversation_chunks` insert가 전부 `NoReferencedTableError`로 실패하는 것을
발견했다. DB에는 Alembic 마이그레이션으로 `photos` 테이블이 이미 존재하지만,
SQLAlchemy ORM은 매핑 클래스가 같은 프로세스에서 import돼 있어야 FK를 해석한다.

`linked_chunk_id`(photos → conversation_chunks)는 ORM에 FK로 선언하지 않았다 —
erd.md §1 "의도적 비정규화 2"(양방향 FK)가 실제 DB에는 있지만, 두 테이블을 서로
`ForeignKey(...)`로 선언하면 SQLAlchemy가 순환 의존으로 처리해야 해서 불필요한
복잡도가 생긴다. 이 프로젝트는 아직 ORM `relationship()`을 전혀 쓰지 않고
Repository로만 조회하므로, ORM 레벨 FK 선언은 실질적 이득이 없다 — 실제 무결성은
DB 제약(Alembic DDL)이 이미 보장한다.

TODO(다음 스프린트): application/api 계층 구현 — 사진 업로드(Presigned URL,
sync-contract.md §4), AI 인라인 편입 제안(placement_status=proposed) 등.
"""
