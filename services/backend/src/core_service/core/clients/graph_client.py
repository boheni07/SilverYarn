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

    async def close(self) -> None:
        await self._driver.close()
