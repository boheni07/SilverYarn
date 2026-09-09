"""애플리케이션 레벨 PII 필드 암호화 — schema.md §5, decisions.md #45, CTO 검토 B4.

## 이번 라운드 대상 (5개 초민감 자유텍스트 컬럼)
  - `chapters.body_text`
  - `chapter_revisions.body_text_snapshot`
  - `conversation_chunks.transcript_on_device` / `transcript_server` / `assistant_response`

`name` / `contact` / `birth_date`는 부분일치 검색·컬럼 타입 변경(blind index, DATE→BYTEA)이
얽혀 있어 다음 라운드로 분리했다(decisions.md #45).

## 설계 (CTO B4 권고 中 ②·③)
  - **사용자별 DEK**(Data Encryption Key): `user_encryption_keys` 테이블에 KEK로 랩핑해 저장.
    사용자 파기 시 이 행만 지우면 해당 사용자의 모든 PII 자유텍스트가 복호화 불가능해진다
    (crypto-shredding — B3 보유기간/파기 정책의 파기 수단, 법무 확인 대기).
  - **KEK**(Key Encryption Key): 환경변수 `PII_KEK`(임시). 온프레미스 Vault 이전 시
    `PiiCrypto` 생성 지점만 교체하면 된다. 회전 대비로 MultiFernet(콤마 구분 다중 키).
  - **알고리즘**: Fernet(AES-128-CBC + HMAC-SHA256, `cryptography` 패키지).
  - **토큰 포맷**: `pii.v1.` 접두사 + Fernet 토큰. 접두사로 평문/암호문을 구분하므로
    (1) 로컬 개발 DB의 기존 평문 행은 복호화 시 그대로 통과하고 (2) 재저장 시 암호화된다.
    운영 데이터는 처음부터 암호문만 존재한다.

## 경계
  repository 계층에서만 encrypt/decrypt한다(도메인·application은 평문만 본다).
  DEK 캐시는 `AsyncSession.info`에 두어 요청(트랜잭션) 수명과 함께 폐기된다 —
  롤백된 트랜잭션이 만든 DEK가 프로세스 캐시에 남아 다음 요청을 오염시키는 문제를 피한다.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from datetime import datetime
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from sqlalchemy import DateTime, LargeBinary, SmallInteger, func, select
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.config import Settings, get_settings
from core_service.core.db import Base

logger = logging.getLogger(__name__)

_TOKEN_PREFIX = "pii.v1."
_SESSION_CACHE_KEY = "_pii_deks"

_KEK_MISSING_MSG = (
    "PII_KEK 환경변수가 비어 있습니다. PII 자유텍스트 컬럼(schema.md §5)을 다루려면 "
    "KEK가 필요합니다. 다음으로 하나 생성해 .env.local / 시크릿 매니저에 넣으세요:\n"
    '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
)


class UserEncryptionKeyModel(Base):
    """사용자별 DEK 저장소 — 도메인 엔티티가 아니라 순수 암호화 인프라 테이블이다
    (schema.md §5의 17개 엔티티에 포함되지 않는 부속 테이블, decisions.md #45).

    `dek_wrapped`는 평문 DEK(Fernet 키)를 KEK로 암호화한 것. KEK가 회전하면
    이 컬럼만 재랩핑하면 되고 실제 PII 컬럼은 건드리지 않는다.
    """

    __tablename__ = "user_encryption_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    dek_wrapped: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PiiCrypto:
    """KEK 기반 DEK 랩핑 + DEK 기반 필드 암복호화. 상태가 없어 프로세스 싱글턴으로 공유한다."""

    def __init__(self, kek_keys: list[str]):
        if not kek_keys:
            raise RuntimeError(_KEK_MISSING_MSG)
        try:
            fernets = [Fernet(k.strip().encode()) for k in kek_keys]
        except (ValueError, TypeError) as exc:  # 잘못된 키 포맷
            raise RuntimeError(f"PII_KEK 형식이 올바른 Fernet 키가 아닙니다: {exc}") from exc
        self._kek = MultiFernet(fernets)
        # blind index(동등검색용 HMAC) 키 — **첫 KEK에서만** 유도한다. KEK 회전 시에도
        # 첫 KEK를 목록 마지막에 남겨두면 인덱스가 유지되고, 첫 KEK를 완전히 폐기하려면
        # contact_bidx 백필 배치가 필요하다(decisions.md #45 2차 — 임시 방식).
        self._bidx_key = hashlib.blake2b(
            kek_keys[0].strip().encode(), person=b"silveryarn-bidx", digest_size=32
        ).digest()

    @classmethod
    def from_settings(cls, settings: Settings) -> PiiCrypto:
        keys = [k for k in settings.pii_kek.split(",") if k.strip()]
        return cls(keys)

    # --- DEK 수명주기 ---
    @staticmethod
    def generate_dek() -> bytes:
        return Fernet.generate_key()

    def wrap_dek(self, dek: bytes) -> bytes:
        return self._kek.encrypt(dek)

    def unwrap_dek(self, wrapped: bytes) -> bytes:
        return self._kek.decrypt(wrapped)

    # --- 필드 암복호화 ---
    def encrypt_field(self, dek: bytes, plaintext: str) -> str:
        token = Fernet(dek).encrypt(plaintext.encode()).decode()
        return f"{_TOKEN_PREFIX}{token}"

    # --- blind index (동등검색 전용, decisions.md #45 2차 / CTO B4) ---
    def blind_index(self, value: str) -> str:
        """정규화된 값의 HMAC-SHA256(hex). 같은 평문 → 같은 인덱스이므로 `WHERE bidx = ?`로
        동등검색만 가능하다(부분검색·정렬 불가). 원문은 복원 불가."""
        normalized = " ".join(value.split()).strip().casefold()
        return hmac.new(self._bidx_key, normalized.encode(), hashlib.sha256).hexdigest()

    def decrypt_field(self, dek: bytes, stored: str) -> str:
        if not stored.startswith(_TOKEN_PREFIX):
            # 로컬 개발 DB의 암호화 이전 평문 행 — 그대로 통과시키고 한 번 경고한다.
            logger.warning(
                "PII 컬럼에서 평문 값을 발견했습니다(암호화 접두사 없음). 로컬 개발 데이터로 "
                "간주하고 통과시킵니다 — 운영에서는 발생하면 안 됩니다."
            )
            return stored
        token = stored[len(_TOKEN_PREFIX) :].encode()
        try:
            return Fernet(dek).decrypt(token).decode()
        except InvalidToken as exc:
            raise RuntimeError(
                "PII 필드 복호화 실패 — DEK 불일치 또는 데이터 손상. KEK 회전/복원 이력을 확인하세요."
            ) from exc


class DekResolver:
    """user_id → 평문 DEK. 없으면 생성해 저장한다. 캐시는 세션(트랜잭션) 스코프."""

    def __init__(self, crypto: PiiCrypto):
        self._crypto = crypto

    async def resolve(self, session: AsyncSession, user_id: uuid.UUID) -> bytes:
        cache: dict[uuid.UUID, bytes] = session.info.setdefault(_SESSION_CACHE_KEY, {})
        cached = cache.get(user_id)
        if cached is not None:
            return cached

        row = await session.get(UserEncryptionKeyModel, user_id)
        if row is None:
            dek = await self._create(session, user_id)
        else:
            dek = self._crypto.unwrap_dek(row.dek_wrapped)

        cache[user_id] = dek
        return dek

    async def _create(self, session: AsyncSession, user_id: uuid.UUID) -> bytes:
        dek = self._crypto.generate_dek()
        wrapped = self._crypto.wrap_dek(dek)
        try:
            # SAVEPOINT로 감싸 동시 요청이 같은 user_id로 먼저 INSERT한 경우에도
            # 바깥 트랜잭션을 살린 채 회복한다.
            async with session.begin_nested():
                session.add(UserEncryptionKeyModel(user_id=user_id, dek_wrapped=wrapped))
        except IntegrityError:
            existing = await session.execute(
                select(UserEncryptionKeyModel).where(UserEncryptionKeyModel.user_id == user_id)
            )
            row = existing.scalar_one()
            return self._crypto.unwrap_dek(row.dek_wrapped)
        return dek


class PiiFieldEncryptor:
    """repository가 주입받는 파사드 — encrypt/decrypt에 필요한 DEK 조회를 감춘다."""

    def __init__(self, crypto: PiiCrypto, resolver: DekResolver):
        self._crypto = crypto
        self._resolver = resolver

    async def encrypt(self, session: AsyncSession, user_id: uuid.UUID, plaintext: str) -> str:
        dek = await self._resolver.resolve(session, user_id)
        return self._crypto.encrypt_field(dek, plaintext)

    async def encrypt_opt(
        self, session: AsyncSession, user_id: uuid.UUID, plaintext: str | None
    ) -> str | None:
        if plaintext is None:
            return None
        return await self.encrypt(session, user_id, plaintext)

    async def decrypt(self, session: AsyncSession, user_id: uuid.UUID, stored: str) -> str:
        dek = await self._resolver.resolve(session, user_id)
        return self._crypto.decrypt_field(dek, stored)

    async def decrypt_opt(self, session: AsyncSession, user_id: uuid.UUID, stored: str | None) -> str | None:
        if stored is None:
            return None
        return await self.decrypt(session, user_id, stored)

    def blind_index(self, value: str) -> str:
        """동등검색용 HMAC(hex). user_id 불필요(전역 키). `contact` 검색·중복확인용."""
        return self._crypto.blind_index(value)


@lru_cache
def get_pii_encryptor() -> PiiFieldEncryptor:
    """프로세스 싱글턴. `PII_KEK`가 비어 있으면 여기서 RuntimeError.

    repository __init__의 기본값으로만 쓰이므로(모듈 import 시점이 아님) `PII_KEK` 없이도
    앱/워커 기동과 CI(실 DB 미접속, Fake repository 단위 테스트)는 영향받지 않는다.
    """
    crypto = PiiCrypto.from_settings(get_settings())
    return PiiFieldEncryptor(crypto, DekResolver(crypto))
