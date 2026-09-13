"""`GET /me` 유닛 테스트 — `require_auth`를 오버라이드해 실 Keycloak 검증·DB 조회
없이 라우터 자체의 직렬화만 검증한다(core/test_errors.py와 동일한 TestClient 패턴).
"""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core_service.auth_deps import AuthContext, require_auth
from core_service.core.auth import Membership
from core_service.modules.family_members.api.v1.me import router
from core_service.shared.domain_enums import FamilyRole


def _client(ctx: AuthContext) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: ctx
    return TestClient(app)


def test_me_returns_single_membership() -> None:
    user_id = uuid.uuid4()
    family_member_id = uuid.uuid4()
    ctx = AuthContext(
        subject="keycloak-sub-1",
        is_2fa=True,
        memberships=[
            Membership(
                family_member_id=family_member_id,
                user_id=user_id,
                role=FamilyRole.FAMILY,
                two_factor_enabled=True,
            )
        ],
    )

    response = _client(ctx).get("/me")

    assert response.status_code == 200
    memberships = response.json()["data"]["memberships"]
    assert len(memberships) == 1
    assert memberships[0]["user_id"] == str(user_id)
    assert memberships[0]["family_member_id"] == str(family_member_id)
    assert memberships[0]["role"] == "family"
    assert memberships[0]["org_id"] is None


def test_me_returns_multiple_memberships_when_connected_to_several_elders() -> None:
    ctx = AuthContext(
        subject="keycloak-sub-2",
        is_2fa=False,
        memberships=[
            Membership(
                family_member_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                role=FamilyRole.CAREGIVER,
                two_factor_enabled=False,
                org_id=uuid.uuid4(),
            ),
            Membership(
                family_member_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                role=FamilyRole.FAMILY,
                two_factor_enabled=False,
            ),
        ],
    )

    response = _client(ctx).get("/me")

    assert response.status_code == 200
    memberships = response.json()["data"]["memberships"]
    assert len(memberships) == 2
    assert memberships[0]["role"] == "caregiver"
    assert memberships[0]["org_id"] is not None
    assert memberships[1]["org_id"] is None
