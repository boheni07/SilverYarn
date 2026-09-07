"""care 모듈 — 말벗돌봄 모드.

conversation_chunks: 4계층 구현 완료 — users/devices/author/family_members/
invitations와 동일한 참조 패턴. Append-Only 엔티티라 Repository에 update가 없다
(sync-contract.md §3 충돌정책: "충돌 없음"). `record_chunk()`는 author의
`save_draft()`와 같은 성격으로 worker.py 파이프라인이 호출할 자리이며(TODO,
미연결) 공개 POST 엔드포인트로 노출하지 않는다 — 청크는 클라이언트가 직접 만드는
리소스가 아니라 업로드 파이프라인의 산출물이다.

검색(`search_chunks`)은 임시 DB ILIKE 구현이다 — 실제로는 design.md §2.4의
Qdrant 하이브리드 서치(BM25+Dense, decisions.md #28)로 교체해야 하며, 이는
`rag-core` 논리 모듈(아직 미착수)의 책임이다.

TODO(다음 스프린트):
- emotion_alerts/emotion_scores: Phase 1 피처플래그 OFF(decisions.md #25) — 이번
  라운드에서 구현하지 않음. 법무 검토(#12) 완료 전까지 write 경로를 열지 않는다.
- worker.py의 process_upload 잡에서 record_chunk() 실제 호출 연결
설계 근거: workflow-diagrams.md §2(온디바이스 파이프라인)·§3(배치 동기화).
"""
