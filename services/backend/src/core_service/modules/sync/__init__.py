"""sync 모듈 — Wi-Fi 배치 동기화(sync-contract.md).

`SyncService`(application/)는 업로드 접수(세션 생성 + arq 잡 enqueue)와 상태 조회만
담당한다. 실제 파이프라인(STT 재전사 → 지식추출 → 임베딩/그래프 적재 → 챕터 갱신)은
`UploadPipelineService`가 맡고, `worker.py`(패키지 최상위)의 `process_upload` 잡이
그것을 실행한다 — 이 모듈 자체에는 잡 함수가 없다(워커 진입점은 core_service 패키지
전체에 하나뿐이므로).

다운로드(`GET /sync/download`)는 여전히 빈 스냅샷 골격이다 — chapter_updates 등
실제 조회는 다음 스프린트.
"""
