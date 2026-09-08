# local/vectorstore/

의도적으로 비어 있다 — decisions.md #32가 경량 VectorDB(임베딩 기반 의미검색)를
**고사양(일반 모드) 단말 한정 Phase 2+ 검토 대상**으로 확정했다. Phase 1은
`local/db/AutobiographyFtsStore`의 SQLite FTS5(BM25 키워드 검색) 단독으로 동작한다.

Phase 2+에서 이 패키지를 채울 때 참고할 것: CONVENTIONS.md §2.2.1의 "로컬 RAG"
행, design.md §2.1.
