"""온프레미스 AI 인프라 클라이언트 — Whisper(STT)/BGE-M3(Embedding)/vLLM(LLM)/
Qdrant(VectorDB)/Neo4j(Graph). 모두 CONVENTIONS.md §4 접두사(STT_/EMBEDDING_/LLM_/
VECTORDB_/GRAPH_)로 접속 정보를 읽는다.

⚠️ **실제 서비스가 아직 없다**: 이 디렉터리의 클라이언트는 design.md §2.11이
서술한 파이프라인 형태(재전사→지식추출→임베딩/그래프 적재)를 코드로 표현하되,
각 서비스의 실제 REST/SDK 스펙은 온프레미스 인프라 구축 전까지 추정치다.
Qdrant(qdrant-client)·Neo4j(neo4j 공식 드라이버)는 SDK가 확정돼 있어 그대로
썼지만, STT/Embedding/LLM(vLLM)은 REST 계약이 아직 없어 "이런 모양일 것"이라는
가정 하에 작성했다 — 실 서비스 배포 시 이 파일들만 교체하면 되도록 인터페이스를
좁게(메서드 1~2개) 유지했다.
"""
