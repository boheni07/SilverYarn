"""BLIND_INDEX_KEY를 새로 설정했을 때 기존 `contact_bidx` 값을 재계산 — decisions.md #60.

배경: 이전에는 blind index 키가 `PII_KEK` 첫 키에서 유도됐다("하나 유출 시 둘 다
노출"되는 결함). #60에서 전용 `BLIND_INDEX_KEY`로 분리했지만, 이미 저장된
`contact_bidx` 값은 옛 키로 계산된 것이라 새 키로 만든 `PiiCrypto.blind_index()`
결과와 더 이상 일치하지 않는다 — 이 스크립트가 그 재계산을 수행한다.

실행 순서:
    1. 새 `BLIND_INDEX_KEY`를 생성해 .env.local / 시크릿 매니저에 설정
       (PII_KEK와 반드시 다른 값 — CONVENTIONS.md §4):
         python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    2. 이 스크립트 실행:
         cd services/backend && PYTHONPATH=src python scripts/backfill_blind_index.py
    3. 완료 후 family_members·invitations의 `contact_bidx`가 새 키 기준으로
       재계산된다. 이때부터 동등검색(`WHERE contact_bidx = ?`)이 다시 정상 동작한다.

이 스크립트를 건너뛰고 BLIND_INDEX_KEY만 설정하면, 새로 생성되는 행의
contact_bidx는 새 키로 계산되지만 기존 행은 옛 키 그대로 남아 서로 어긋난다
(초대 중복확인이 기존 사용자를 못 찾는 등) — 반드시 함께 실행할 것.
"""

import asyncio

from sqlalchemy import select

from core_service.core import model_registry  # noqa: F401  (모든 모델 등록 — FK 해석)
from core_service.core.crypto import get_pii_encryptor
from core_service.core.db import get_session_factory
from core_service.modules.family_members.infrastructure.family_member_repository import (
    FamilyMemberModel,
)
from core_service.modules.invitations.infrastructure.invitation_repository import (
    InvitationModel,
)


async def _backfill_family_members() -> int:
    pii = get_pii_encryptor()
    sf = get_session_factory()
    updated = 0
    async with sf() as session:
        rows = (await session.execute(select(FamilyMemberModel))).scalars().all()
        for row in rows:
            plaintext = await pii.decrypt(session, row.user_id, row.contact)
            new_bidx = pii.blind_index(plaintext)
            if new_bidx != row.contact_bidx:
                row.contact_bidx = new_bidx
                updated += 1
        await session.commit()
    return updated


async def _backfill_invitations() -> int:
    pii = get_pii_encryptor()
    sf = get_session_factory()
    updated = 0
    async with sf() as session:
        rows = (await session.execute(select(InvitationModel))).scalars().all()
        for row in rows:
            plaintext = await pii.decrypt(session, row.user_id, row.contact)
            new_bidx = pii.blind_index(plaintext)
            if new_bidx != row.contact_bidx:
                row.contact_bidx = new_bidx
                updated += 1
        await session.commit()
    return updated


async def main() -> None:
    fm_count = await _backfill_family_members()
    print(f"family_members.contact_bidx 재계산: {fm_count}건 갱신")
    inv_count = await _backfill_invitations()
    print(f"invitations.contact_bidx 재계산: {inv_count}건 갱신")


if __name__ == "__main__":
    asyncio.run(main())
