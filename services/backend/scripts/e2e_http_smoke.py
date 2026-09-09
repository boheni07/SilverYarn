"""HTTP 레이어 스모크 — 부트스트랩 엔드포인트 + Device Token + access_logs 미들웨어.

실행:
    cd services/backend
    PYTHONPATH=src python -m uvicorn core_service.main:app --port 9677 &   # 8000은 다른 스택이 쓸 수 있음
    E2E_BASE_URL=http://127.0.0.1:9677 PYTHONPATH=src python scripts/e2e_http_smoke.py

전제: infra 스택 기동 + `alembic upgrade head`. Keycloak이 없어 가족 토큰
(require_family) 경로는 여기서 검증하지 않는다(그 경로는 tests/core/test_auth.py의
RS256 검증 유닛테스트로 커버).
"""

import asyncio
import os

import httpx
from sqlalchemy import text

from core_service.core import model_registry  # noqa: F401
from core_service.core.db import get_session_factory

BASE = f"{os.environ.get('E2E_BASE_URL', 'http://127.0.0.1:9677')}/api/v1"
results: list[tuple[bool, str]] = []


def check(ok: bool, msg: str) -> None:
    results.append((ok, msg))
    print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as c:
        # 1. POST /users — 부트스트랩(무인증)
        r = await c.post(f"{BASE}/users", json={"name": "이순자", "birth_date": "1940-01-01"})
        check(r.status_code == 201, f"POST /users → 201 (got {r.status_code})")
        user_id = r.json()["data"]["id"]
        check(r.json()["data"]["birth_date"] == "1940-01-01", "응답 birth_date는 평문 date")

        # 2. POST /devices — 부트스트랩, Device Token 1회 발급
        r = await c.post(
            f"{BASE}/devices",
            json={"display_id": "MB-0001", "user_id": user_id, "ram_gb": 8.0, "android_version": "14"},
        )
        check(r.status_code == 201, f"POST /devices → 201 (got {r.status_code})")
        body = r.json()["data"]
        token = body["device_token"]
        check(len(token) > 20, f"device_token 발급 (len={len(token)})")
        check(
            body["install_mode"] == "normal",
            f"install_mode=normal (RAM 8/API 14) (got {body['install_mode']})",
        )

        # 3. GET consent-logs 무인증 → 401
        r = await c.get(f"{BASE}/users/{user_id}/consent-logs")
        check(r.status_code == 401, f"GET consent-logs 무인증 → 401 (got {r.status_code})")

        # 4. POST consent-logs with X-Device-Token
        r = await c.post(
            f"{BASE}/users/{user_id}/consent-logs",
            headers={"X-Device-Token": token},
            json={"consent_type": "data_collection", "granted": True},
        )
        check(r.status_code == 201, f"POST consent-logs (Device Token) → 201 (got {r.status_code})")
        check(r.json()["data"]["actor"] == "self", "consent actor=self (granted_by 없음)")

        # 5. 잘못된 Device Token → 401
        r = await c.get(
            f"{BASE}/sync/download",
            params={"device_id": body["id"]},
            headers={"X-Device-Token": "bogus-token"},
        )
        check(r.status_code == 401, f"잘못된 Device Token → 401 (got {r.status_code})")

        # 6. 유효 토큰 + 다른 device_id → 403 (IDOR 방지)
        r = await c.get(
            f"{BASE}/sync/download",
            params={"device_id": "00000000-0000-0000-0000-000000000000"},
            headers={"X-Device-Token": token},
        )
        check(r.status_code == 403, f"토큰≠device_id → 403 (got {r.status_code})")

        # 7. 유효 토큰 + 자기 device_id → 200
        r = await c.get(
            f"{BASE}/sync/download",
            params={"device_id": body["id"]},
            headers={"X-Device-Token": token},
        )
        check(r.status_code == 200, f"토큰=device_id → 200 (got {r.status_code})")

    # 8. access_logs 미들웨어가 적재했는가
    async with get_session_factory()() as s:
        n = (await s.execute(text("SELECT count(*) FROM access_logs"))).scalar_one()
        kinds = (await s.execute(text("SELECT DISTINCT actor_kind FROM access_logs"))).scalars().all()
        sample = (
            await s.execute(
                text(
                    "SELECT method, path, status_code, actor_kind FROM access_logs "
                    "ORDER BY created_at DESC LIMIT 3"
                )
            )
        ).all()
        await s.execute(text("DELETE FROM users WHERE id=:i"), {"i": user_id})
        await s.commit()
    check(n >= 7, f"access_logs {n}행 적재 (제8조 감사로그)")
    check("device" in kinds and "anonymous" in kinds, f"actor_kind 구분됨: {sorted(kinds)}")
    print("    최근 3건:", sample)

    print()
    passed = sum(1 for ok, _ in results if ok)
    print(f"=== {passed}/{len(results)} PASS ===")
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
