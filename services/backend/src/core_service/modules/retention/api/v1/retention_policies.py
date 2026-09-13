"""retention_policies 리소스 라우터 — decisions.md #56(Q5), apps/admin "보유기간
설정" 화면용. 보유기간 자체가 법무·정책 판단이라 admin 전용."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core_service.auth_deps import require_roles
from core_service.modules.retention.application.retention_policy_service import (
    RetentionPolicyService,
)
from core_service.modules.retention.deps import get_retention_policy_service
from core_service.shared.domain_enums import FamilyRole
from core_service.shared.schemas import DataResponse

router = APIRouter(prefix="/retention-policies", tags=["retention-policies"])


class RetentionPolicyResponse(BaseModel):
    id: uuid.UUID
    category: str
    retention_days: int
    updated_at: datetime


class RetentionPolicyUpdateRequest(BaseModel):
    retention_days: int


def _to_response(policy) -> RetentionPolicyResponse:  # noqa: ANN001 — RetentionPolicy 도메인 dataclass
    return RetentionPolicyResponse(
        id=policy.id,
        category=policy.category,
        retention_days=policy.retention_days,
        updated_at=policy.updated_at,
    )


@router.get("", response_model=DataResponse[list[RetentionPolicyResponse]])
async def list_retention_policies(
    service: RetentionPolicyService = Depends(get_retention_policy_service),
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> DataResponse[list[RetentionPolicyResponse]]:
    policies = await service.list_policies()
    return DataResponse(data=[_to_response(p) for p in policies])


@router.put("/{category}", response_model=DataResponse[RetentionPolicyResponse])
async def update_retention_policy(
    category: str,
    body: RetentionPolicyUpdateRequest,
    service: RetentionPolicyService = Depends(get_retention_policy_service),
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> DataResponse[RetentionPolicyResponse]:
    policy = await service.set_retention_days(category, body.retention_days)
    return DataResponse(data=_to_response(policy))
