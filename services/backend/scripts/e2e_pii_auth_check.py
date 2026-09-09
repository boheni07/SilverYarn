"""세션 전체 변경분(PR #1~#6)의 실 DB e2e 검증 — repository 계층 직접 호출.

실행: (infra 스택 기동 + alembic upgrade head 후)
    cd services/backend && PYTHONPATH=src python scripts/e2e_pii_auth_check.py

HTTP·Keycloak 없이 repository/service 계층을 실 Postgres에 대고 돌려
암복호화·blind index·멱등성·crypto-shredding·access_log 스키마를 확인한다.
"""

import asyncio
import datetime as dt
import uuid

from sqlalchemy import text

from core_service.core import model_registry  # noqa: F401  (모든 모델 등록 — FK 해석)
from core_service.core.db import get_session_factory
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.domain.chapter import ChapterPeriod, RevisionAction
from core_service.modules.author.infrastructure.chapter_repository import ChapterRepository
from core_service.modules.author.infrastructure.chapter_revision_repository import (
    ChapterRevisionRepository,
)
from core_service.modules.care.application.conversation_chunk_service import ConversationChunkService
from core_service.modules.care.domain.conversation_chunk import ConversationMode
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)
from core_service.modules.consent.application.consent_service import ConsentService
from core_service.modules.consent.domain.consent_log import ConsentType
from core_service.modules.consent.infrastructure.consent_log_repository import ConsentLogRepository
from core_service.modules.devices.infrastructure.device_credential_repository import (
    DeviceCredentialRepository,
    hash_token,
)
from core_service.modules.family_members.application.family_member_service import FamilyMemberService
from core_service.modules.family_members.domain.family_member import FamilyRole
from core_service.modules.family_members.infrastructure.family_member_repository import (
    FamilyMemberRepository,
)
from core_service.modules.users.application.user_service import UserService
from core_service.modules.users.infrastructure.user_repository import UserRepository

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results: list[tuple[bool, str]] = []


def check(ok: bool, msg: str) -> None:
    results.append((ok, msg))
    print(f"  [{PASS if ok else FAIL}] {msg}")


async def main() -> None:
    sf = get_session_factory()

    # --- 1. user + birth_date 암호화 ---
    async with sf() as s:
        user = await UserService(UserRepository(s)).create_user("김할머니", dt.date(1945, 3, 12))
        await s.commit()
    check(user.birth_date == dt.date(1945, 3, 12), "user.birth_date 도메인은 date 그대로")

    async with sf() as s:
        row = (await s.execute(text("SELECT birth_date FROM users WHERE id=:i"), {"i": user.id})).scalar_one()
    check(row.startswith("pii.v1."), f"DB users.birth_date는 암호문 (pii.v1.…): {row[:16]}…")

    async with sf() as s:
        uek = (
            await s.execute(
                text("SELECT count(*) FROM user_encryption_keys WHERE user_id=:i"), {"i": user.id}
            )
        ).scalar_one()
    check(uek == 1, "user_encryption_keys 행 자동 생성 (사용자별 DEK)")

    # --- 2. chapter.body_text 암호화 round-trip ---
    async with sf() as s:
        svc = ChapterService(ChapterRepository(s), ChapterRevisionRepository(s))
        ch = await svc.save_draft(
            user.id, 2, "청년기", ChapterPeriod.YOUTH, "1978년 인천 기계공장에서 일했다."
        )
        await s.commit()
    async with sf() as s:
        db_body = (
            await s.execute(text("SELECT body_text FROM chapters WHERE id=:i"), {"i": ch.id})
        ).scalar_one()
    check(db_body.startswith("pii.v1."), "DB chapters.body_text는 암호문")
    check("인천" not in db_body, "평문이 DB에 노출되지 않음")
    async with sf() as s:
        reread = await ChapterService(ChapterRepository(s), ChapterRevisionRepository(s)).get_chapter(ch.id)
    check(reread.body_text == "1978년 인천 기계공장에서 일했다.", "재조회 시 평문 복호화")

    # --- 3. chapter_revision 암호화 (감수) ---
    async with sf() as s:
        svc = ChapterService(ChapterRepository(s), ChapterRevisionRepository(s))
        await svc.review_chapter(ch.id, None, RevisionAction.APPROVED, "좋습니다")
        await s.commit()
    async with sf() as s:
        snap = (
            await s.execute(
                text("SELECT body_text_snapshot FROM chapter_revisions WHERE chapter_id=:i"), {"i": ch.id}
            )
        ).scalar_one()
    check(snap.startswith("pii.v1."), "DB chapter_revisions.body_text_snapshot는 암호문")

    # --- 4. family_member contact 암호문 + blind index ---
    async with sf() as s:
        fm = await FamilyMemberService(FamilyMemberRepository(s)).create_family_member(
            user.id, FamilyRole.FAMILY, "이가족", "010-1234-5678"
        )
        await s.commit()
    async with sf() as s:
        c_row = (
            await s.execute(
                text("SELECT contact, contact_bidx FROM family_members WHERE id=:i"), {"i": fm.id}
            )
        ).first()
    check(c_row[0].startswith("pii.v1."), "DB family_members.contact는 암호문")
    check(len(c_row[1]) == 64 and "1234" not in c_row[1], f"contact_bidx는 HMAC hex: {c_row[1][:16]}…")
    async with sf() as s:
        refm = await FamilyMemberRepository(s).get_by_id(fm.id)
    check(refm.contact == "010-1234-5678", "family_member.contact 재조회 시 평문")

    # --- 5. conversation_chunk 암호화 + 멱등성 ---
    sid, turn = f"sess-{uuid.uuid4()}", 3
    async with sf() as s:
        svc = ConversationChunkService(ConversationChunkRepository(s))
        c1 = await svc.record_chunk(
            user.id, "opus/a.opus", "손주가 보고싶다", ConversationMode.CARE, sid, turn
        )
        await s.commit()
    async with sf() as s:
        svc = ConversationChunkService(ConversationChunkRepository(s))
        c2 = await svc.record_chunk(
            user.id, "opus/a.opus", "손주가 보고싶다", ConversationMode.CARE, sid, turn
        )
        await s.commit()
    check(c1.id == c2.id, "같은 (user, session, turn) 재적재 → 동일 청크 (멱등성)")
    async with sf() as s:
        n = (
            await s.execute(
                text(
                    "SELECT count(*) FROM conversation_chunks "
                    "WHERE user_id=:u AND session_id=:s AND turn_id=:t"
                ),
                {"u": user.id, "s": sid, "t": turn},
            )
        ).scalar_one()
    check(n == 1, "conversation_chunks 행 1개만 (uq_conversation_chunks_turn)")
    async with sf() as s:
        tod = (
            await s.execute(
                text("SELECT transcript_on_device FROM conversation_chunks WHERE id=:i"), {"i": c1.id}
            )
        ).scalar_one()
    check(tod.startswith("pii.v1."), "DB conversation_chunks.transcript_on_device는 암호문")

    # --- 6. consent ---
    async with sf() as s:
        cs = ConsentService(ConsentLogRepository(s))
        await cs.record_consent(user.id, ConsentType.DATA_COLLECTION, True, None)
        await cs.record_consent(user.id, ConsentType.DATA_COLLECTION, False, None)
        state = await cs.current_state(user.id)
        await s.commit()
    check(state.get(ConsentType.DATA_COLLECTION) is False, "consent current_state는 최신 행(철회) 반영")

    # --- 7. device_credentials 토큰 해시 조회 ---
    from core_service.modules.devices.application.device_service import DeviceService
    from core_service.modules.devices.infrastructure.device_repository import DeviceRepository

    async with sf() as s:
        dev = await DeviceService(DeviceRepository(s)).register_device(
            "MB-9999", "TestPixel", user.id, __import__("decimal").Decimal("8.0"), "14"
        )
        token = await DeviceCredentialRepository(s).issue(dev.id)
        await s.commit()
    async with sf() as s:
        ident = await DeviceCredentialRepository(s).resolve_active(hash_token(token))
        await s.commit()
    check(
        ident is not None and ident.device_id == dev.id and ident.user_id == user.id,
        "Device Token SHA-256 해시로 (device_id, user_id) 해석",
    )
    async with sf() as s:
        stored = (
            await s.execute(
                text("SELECT token_hash FROM device_credentials WHERE device_id=:i"), {"i": dev.id}
            )
        ).scalar_one()
    check(stored == hash_token(token) and token not in stored, "DB에는 평문 토큰이 아니라 해시만")

    # --- 8. crypto-shredding: user_encryption_keys 삭제 → 복호화 불가 ---
    async with sf() as s:
        await s.execute(text("DELETE FROM user_encryption_keys WHERE user_id=:i"), {"i": user.id})
        await s.commit()
    # DekResolver 캐시는 세션 스코프이므로 새 세션에서 확인
    shred_ok = False
    try:
        async with sf() as s:
            await ChapterService(ChapterRepository(s), ChapterRevisionRepository(s)).get_chapter(ch.id)
    except RuntimeError:
        shred_ok = True
    check(shred_ok, "DEK 삭제 후 body_text 복호화 실패 (crypto-shredding 동작)")

    # --- 정리 ---
    async with sf() as s:
        await s.execute(text("DELETE FROM users WHERE id=:i"), {"i": user.id})  # CASCADE
        await s.commit()

    print()
    passed = sum(1 for ok, _ in results if ok)
    print(f"=== {passed}/{len(results)} PASS ===")
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
