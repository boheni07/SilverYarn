"""questions 리소스 라우터 — design.md §4.2 `GET /users/{userId}/questions`(L-12).

질문 생성(작가 엔진이 다음 인터뷰 질문을 뽑는 흐름)은 아직 미구현이라 조회만 노출한다
(question_repository.py 모듈 docstring 참조). `GET /sync/download`의 `priority_questions`와는
다르다 — 그쪽은 미답변·`since` 이후만, 이쪽은 가족 웹 콘솔이 큐 전체를 보는 용도다.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.auth_deps import AuthContext, authorize_user_access, require_auth
from core_service.core.db import get_db
from core_service.modules.author.application.question_service import QuestionService
from core_service.modules.author.infrastructure.question_repository import QuestionRepository
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["questions"])


class QuestionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    linked_chapter_id: uuid.UUID | None
    text: str
    type: str
    answered: bool
    created_at: datetime


def _service(session: AsyncSession = Depends(get_db)) -> QuestionService:
    return QuestionService(QuestionRepository(session))


@router.get("/users/{user_id}/questions", response_model=DataResponse[list[QuestionResponse]])
async def list_user_questions(
    user_id: uuid.UUID,
    answered: bool | None = None,
    service: QuestionService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[QuestionResponse]]:
    """design.md §4.2 — 회고 질문 큐 조회. `answered`로 필터(생략 시 전체)."""
    authorize_user_access(ctx, user_id)
    questions = await service.list_questions_for_user(user_id, answered)
    return DataResponse(
        data=[
            QuestionResponse(
                id=q.id,
                user_id=q.user_id,
                linked_chapter_id=q.linked_chapter_id,
                text=q.text,
                type=q.type.value,
                answered=q.answered,
                created_at=q.created_at,
            )
            for q in questions
        ]
    )
