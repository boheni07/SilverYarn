"""Neo4j 지식그래프 클라이언트 — decisions.md #29(Neo4j 채택), design.md §2.11.

인물(Person)·사건/청크(ConversationChunk) 노드와 "언급됨" 관계만 다룬다 — 시기별
타임라인·감정 궤적 추적 등 고급 그래프 스키마는 실제 서비스 요구가 구체화된 뒤
설계한다(design.md §2.11의 "관계·타임라인" 서술은 방향성만 제시하고 있음).
"""

from uuid import UUID

from neo4j import AsyncGraphDatabase

from core_service.core.config import get_settings

_UPSERT_QUERY = """
MERGE (c:ConversationChunk {id: $chunk_id})
SET c.user_id = $user_id, c.place = $place, c.period = $period
WITH c
UNWIND $people AS person_name
MERGE (p:Person {name: person_name, user_id: $user_id})
MERGE (p)-[:MENTIONED_IN]->(c)
RETURN c.id AS node_ref
"""


class GraphClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._driver = AsyncGraphDatabase.driver(
            settings.graph_uri, auth=(settings.graph_user, settings.graph_password)
        )

    async def upsert_chunk_node(
        self,
        chunk_id: UUID,
        user_id: UUID,
        people: list[str] | None,
        place: str | None,
        period: str | None,
    ) -> str:
        """청크 노드와 언급된 인물 노드·관계를 적재하고 graph_node_ref(포인터)를 반환."""
        async with self._driver.session() as session:
            result = await session.run(
                _UPSERT_QUERY,
                chunk_id=str(chunk_id),
                user_id=str(user_id),
                people=people or [],
                place=place,
                period=period,
            )
            record = await result.single()
            return record["node_ref"] if record else str(chunk_id)

    async def delete_chunk_node(self, chunk_id: UUID) -> None:
        """decisions.md #56(Q5) — 보유기간 만료된 대화 청크 1건의 노드 삭제.
        MENTIONED_IN 관계도 DETACH DELETE로 함께 지운다. 이 청크만 언급했던
        Person 노드는 고아로 남을 수 있으나(다른 청크가 같은 인물을 또 언급할
        가능성이 있어 함부로 못 지움) design.md 후속 과제로 남긴다."""
        async with self._driver.session() as session:
            await session.run(
                "MATCH (c:ConversationChunk {id: $chunk_id}) DETACH DELETE c", chunk_id=str(chunk_id)
            )

    async def delete_user_nodes(self, user_id: UUID) -> None:
        """decisions.md #56(Q5) — 어르신 계정 전체 삭제(erasure) 시, 이 사용자의
        ConversationChunk·Person 노드를 전부 지운다(둘 다 user_id 프로퍼티로 스코프됨,
        upsert_chunk_node 참조)."""
        async with self._driver.session() as session:
            await session.run("MATCH (n) WHERE n.user_id = $user_id DETACH DELETE n", user_id=str(user_id))

    async def close(self) -> None:
        await self._driver.close()
