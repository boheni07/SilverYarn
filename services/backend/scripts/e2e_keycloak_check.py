"""가족 토큰(Keycloak) 경로 e2e — require_family · authorize_user_access · 2FA · IDOR.

실행:
    (infra 스택 + keycloak 기동, alembic upgrade head, .env.local의 AUTH_ISSUER_URL 설정)
    cd services/backend
    PYTHONPATH=src python -m uvicorn core_service.main:app --port 9677 &
    E2E_BASE_URL=http://127.0.0.1:9677 PYTHONPATH=src python scripts/e2e_keycloak_check.py

테스트 유저는 이 스크립트가 Keycloak admin REST로 idempotent하게 프로비저닝한다
(realm export에는 유저를 넣지 않는다 — 비밀번호 해시가 빠지므로).
"""

import asyncio
import os
import uuid

import httpx
from sqlalchemy import text

from core_service.core import model_registry  # noqa: F401
from core_service.core.config import get_settings
from core_service.core.db import get_session_factory

BASE = f"{os.environ.get('E2E_BASE_URL', 'http://127.0.0.1:9677')}/api/v1"
KC = os.environ.get("KC_BASE_URL", "http://localhost:9678")
REALM = "silveryarn"
PW = "silveryarn_local_dev"
results: list[tuple[bool, str]] = []


def check(ok: bool, msg: str) -> None:
    results.append((ok, msg))
    print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")


async def _admin_token(c: httpx.AsyncClient) -> str:
    r = await c.post(
        f"{KC}/realms/master/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "admin-cli", "username": "admin", "password": "admin"},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def _ensure_user(c: httpx.AsyncClient, admin: str, username: str) -> str:
    """유저를 idempotent하게 만들고 keycloak sub(user id)를 반환."""
    h = {"Authorization": f"Bearer {admin}"}
    existing = (
        await c.get(
            f"{KC}/admin/realms/{REALM}/users", headers=h, params={"username": username, "exact": "true"}
        )
    ).json()
    if existing:
        uid = existing[0]["id"]
    else:
        await c.post(
            f"{KC}/admin/realms/{REALM}/users",
            headers=h,
            json={
                "username": username,
                "enabled": True,
                "emailVerified": True,
                "email": f"{username}@test.local",
                "firstName": "Test",
                "lastName": username,
                "requiredActions": [],
            },
        )
        uid = (
            await c.get(
                f"{KC}/admin/realms/{REALM}/users", headers=h, params={"username": username, "exact": "true"}
            )
        ).json()[0]["id"]
    await c.put(
        f"{KC}/admin/realms/{REALM}/users/{uid}/reset-password",
        headers=h,
        json={"type": "password", "value": PW, "temporary": False},
    )
    return uid


async def _user_token(c: httpx.AsyncClient, username: str) -> str:
    r = await c.post(
        f"{KC}/realms/{REALM}/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "silveryarn-web", "username": username, "password": PW},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def main() -> None:
    settings = get_settings()
    check(
        settings.auth_issuer_url == f"{KC}/realms/{REALM}",
        f"AUTH_ISSUER_URL 설정됨: {settings.auth_issuer_url or '(빈값!)'}",
    )

    async with httpx.AsyncClient(timeout=15.0) as c:
        admin = await _admin_token(c)
        fam_sub = await _ensure_user(c, admin, "family1")
        sw_sub = await _ensure_user(c, admin, "worker1")
        await _ensure_user(c, admin, "unlinked1")

        fam_tok = await _user_token(c, "family1")
        sw_tok = await _user_token(c, "worker1")
        unlinked_tok = await _user_token(c, "unlinked1")

        # --- 어르신 2명 + family_members 링크 + 챕터를 DB에 직접 심는다 ---
        # body_text/contact는 접두사 없는 평문으로 넣어 repository의 "평문 passthrough"
        # 경로를 탄다(암호화 경로는 e2e_pii_auth_check.py가 검증).
        elder_a, elder_b = uuid.uuid4(), uuid.uuid4()
        ins_user = text("INSERT INTO users (id, name, created_at, updated_at) VALUES (:i, :n, now(), now())")
        ins_fm = text(
            "INSERT INTO family_members (id, user_id, role, name, contact, keycloak_sub, created_at) "
            "VALUES (gen_random_uuid(), :u, :r, 'x', 'x', :sub, now())"
        )
        ins_chap = text(
            "INSERT INTO chapters "
            "(id, user_id, chapter_no, title, period, body_text, status, version, updated_at) "
            "VALUES (gen_random_uuid(), :u, 1, 't', 'youth', '테스트 본문', 'draft', 1, now())"
        )
        async with get_session_factory()() as s:
            await s.execute(ins_user, {"i": elder_a, "n": "어르신A"})
            await s.execute(ins_user, {"i": elder_b, "n": "어르신B"})
            await s.execute(ins_fm, {"u": elder_a, "r": "family", "sub": fam_sub})
            await s.execute(ins_fm, {"u": elder_a, "r": "social_worker", "sub": sw_sub})
            await s.execute(ins_chap, {"u": elder_a})
            await s.commit()

        try:
            # 1. 무인증 → 401
            r = await c.get(f"{BASE}/users/{elder_a}/chapters")
            check(r.status_code == 401, f"무인증 챕터 조회 → 401 (got {r.status_code})")

            # 2. 깨진 토큰 → 401
            r = await c.get(f"{BASE}/users/{elder_a}/chapters", headers={"Authorization": "Bearer garbage"})
            check(r.status_code == 401, f"깨진 Bearer → 401 (got {r.status_code})")

            # 3. family1 → 자기 어르신 챕터 → 200
            r = await c.get(
                f"{BASE}/users/{elder_a}/chapters", headers={"Authorization": f"Bearer {fam_tok}"}
            )
            check(r.status_code == 200, f"family1 → elder_A 챕터 → 200 (got {r.status_code})")

            # 4. family1 → 연결 안 된 어르신 → 403 (IDOR)
            r = await c.get(
                f"{BASE}/users/{elder_b}/chapters", headers={"Authorization": f"Bearer {fam_tok}"}
            )
            check(r.status_code == 403, f"family1 → elder_B(미연결) → 403 (got {r.status_code})")

            # 5. worker1(복지사) → elder_A 챕터, third_party_access 동의 없음 → 403
            #    (decisions #54 — 동의 없으면 여전히 막힘. #48의 전면 fail-closed는
            #    #54로 대체됐지만 "동의 없는 상태"의 기본값은 여전히 차단이다)
            r = await c.get(f"{BASE}/users/{elder_a}/chapters", headers={"Authorization": f"Bearer {sw_tok}"})
            check(
                r.status_code == 403,
                f"social_worker(동의 없음) → 챕터 조회 → 403 (got {r.status_code})",
            )

            # 5b. elder_A가 third_party_access 동의 → worker1 재시도 → 200 (decisions #54)
            r = await c.post(
                f"{BASE}/users/{elder_a}/consent-logs",
                headers={"Authorization": f"Bearer {fam_tok}"},
                json={"consent_type": "third_party_access", "granted": True},
            )
            check(r.status_code == 201, f"family1 → third_party_access 동의 기록 → 201 (got {r.status_code})")

            r = await c.get(f"{BASE}/users/{elder_a}/chapters", headers={"Authorization": f"Bearer {sw_tok}"})
            check(
                r.status_code == 200,
                f"social_worker(동의 있음) → 챕터 조회 → 200 (got {r.status_code})",
            )

            # 6. 인증됐지만 어떤 어르신에도 연결 안 된 계정 → 403
            r = await c.get(
                f"{BASE}/users/{elder_a}/chapters", headers={"Authorization": f"Bearer {unlinked_tok}"}
            )
            check(r.status_code == 403, f"미연결 계정 → 403 (got {r.status_code})")

            # 7. family1 → 감수(쓰기, WRITE_ELDER_DATA_ROLES + 2FA) → 챕터 감수. amr=[pwd,mfa]라 통과해야 함
            chap = (
                await c.get(
                    f"{BASE}/users/{elder_a}/chapters", headers={"Authorization": f"Bearer {fam_tok}"}
                )
            ).json()["data"][0]
            r = await c.post(
                f"{BASE}/chapters/{chap['id']}/review",
                headers={"Authorization": f"Bearer {fam_tok}"},
                json={"action": "approved"},
            )
            check(
                r.status_code == 200,
                f"family1 + 2FA(amr) → 챕터 감수 → 200 (got {r.status_code}) {r.text[:120]}",
            )

            # 8. GET /users (admin 전용) → family1은 403
            r = await c.get(f"{BASE}/users", headers={"Authorization": f"Bearer {fam_tok}"})
            check(r.status_code == 403, f"family1 → GET /users(admin 전용) → 403 (got {r.status_code})")

        finally:
            async with get_session_factory()() as s:
                # chapter_revisions.reviewer_id → family_members(id)는 CASCADE가 아니라,
                # users를 지울 때 chapters/family_members CASCADE 순서에 따라 FK 위반이 날 수 있다.
                # 챕터를 먼저 지우면(revisions는 chapter_id CASCADE) 안전하다.
                await s.execute(
                    text("DELETE FROM chapters WHERE user_id IN (:a, :b)"),
                    {"a": elder_a, "b": elder_b},
                )
                await s.execute(text("DELETE FROM users WHERE id IN (:a, :b)"), {"a": elder_a, "b": elder_b})
                await s.commit()

    print()
    passed = sum(1 for ok, _ in results if ok)
    print(f"=== {passed}/{len(results)} PASS ===")
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
