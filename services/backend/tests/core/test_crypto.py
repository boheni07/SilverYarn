"""core/crypto.py 유닛 테스트 — PII 필드 암호화(schema.md §5, decisions.md #45).

DB가 필요한 DekResolver의 INSERT 경로는 로컬 e2e(수기)로 검증한다 — 여기서는
암호화 정합성과 세션 스코프 캐시 로직만 순수하게 검증한다.
"""

import uuid

import pytest
from cryptography.fernet import Fernet

from core_service.core.crypto import (
    DekResolver,
    PiiCrypto,
    PiiFieldEncryptor,
    UserEncryptionKeyModel,
)


@pytest.fixture
def crypto() -> PiiCrypto:
    return PiiCrypto([Fernet.generate_key().decode()])


def test_field_roundtrip(crypto: PiiCrypto) -> None:
    dek = crypto.generate_dek()
    stored = crypto.encrypt_field(dek, "1978년 인천 기계공장에서 김 반장과...")
    assert stored.startswith("pii.v1.")
    assert "인천" not in stored  # 원문이 저장 문자열에 노출되지 않는다
    assert crypto.decrypt_field(dek, stored) == "1978년 인천 기계공장에서 김 반장과..."


def test_plaintext_passthrough(crypto: PiiCrypto) -> None:
    """암호화 접두사가 없는 값(로컬 개발 DB의 기존 평문 행)은 그대로 통과한다."""
    dek = crypto.generate_dek()
    assert crypto.decrypt_field(dek, "암호화 이전 평문") == "암호화 이전 평문"


def test_wrong_dek_raises(crypto: PiiCrypto) -> None:
    stored = crypto.encrypt_field(crypto.generate_dek(), "비밀")
    with pytest.raises(RuntimeError, match="복호화 실패"):
        crypto.decrypt_field(crypto.generate_dek(), stored)


def test_dek_wrap_roundtrip(crypto: PiiCrypto) -> None:
    dek = crypto.generate_dek()
    wrapped = crypto.wrap_dek(dek)
    assert wrapped != dek
    assert crypto.unwrap_dek(wrapped) == dek


def test_multi_kek_rotation() -> None:
    """새 KEK를 앞에 추가해도 옛 KEK로 랩핑된 DEK를 계속 풀 수 있다(MultiFernet)."""
    old_kek = Fernet.generate_key().decode()
    new_kek = Fernet.generate_key().decode()

    old_crypto = PiiCrypto([old_kek])
    dek = old_crypto.generate_dek()
    wrapped_with_old = old_crypto.wrap_dek(dek)

    rotated = PiiCrypto([new_kek, old_kek])  # 첫 키로 암호화, 전체 키로 복호화
    assert rotated.unwrap_dek(wrapped_with_old) == dek


def test_blind_index_is_deterministic_and_normalized(crypto: PiiCrypto) -> None:
    a = crypto.blind_index("010-1234-5678")
    assert a == crypto.blind_index("  010-1234-5678 ")  # 공백 정규화
    assert a == crypto.blind_index("010-1234-5678")
    assert a != crypto.blind_index("010-9999-0000")
    assert len(a) == 64  # sha256 hex
    # 원문 노출 없음 — 정규화된 전체 값이 다이제스트에 그대로 들어 있지 않다.
    # (짧은 4자리 부분문자열 "1234"는 hex 다이제스트에 우연히 나타날 수 있어 검사 대상이 아니다.)
    assert "010-1234-5678" not in a


def test_blind_index_case_folded(crypto: PiiCrypto) -> None:
    assert crypto.blind_index("Family@Example.com") == crypto.blind_index("family@example.com")


def test_empty_kek_raises() -> None:
    with pytest.raises(RuntimeError, match="PII_KEK"):
        PiiCrypto([])


def test_invalid_kek_format_raises() -> None:
    with pytest.raises(RuntimeError, match="Fernet 키"):
        PiiCrypto(["not-a-valid-fernet-key"])


# --- DekResolver: 세션 스코프 캐시 + 기존 행 조회 ---


class _FakeSession:
    """DekResolver가 쓰는 최소 인터페이스만 흉내낸다."""

    def __init__(self, existing: dict[uuid.UUID, UserEncryptionKeyModel] | None = None) -> None:
        self.info: dict[str, object] = {}
        self._rows = existing or {}
        self.added: list[UserEncryptionKeyModel] = []
        self.get_calls = 0

    async def get(self, _model: type, pk: uuid.UUID) -> UserEncryptionKeyModel | None:
        self.get_calls += 1
        return self._rows.get(pk)


async def test_resolver_caches_within_session(crypto: PiiCrypto) -> None:
    user_id = uuid.uuid4()
    dek = crypto.generate_dek()
    row = UserEncryptionKeyModel(user_id=user_id, dek_wrapped=crypto.wrap_dek(dek))
    session = _FakeSession({user_id: row})
    resolver = DekResolver(crypto)

    first = await resolver.resolve(session, user_id)  # type: ignore[arg-type]
    second = await resolver.resolve(session, user_id)  # type: ignore[arg-type]

    assert first == dek
    assert second == dek
    assert session.get_calls == 1  # 두 번째는 캐시 히트


async def test_field_encryptor_roundtrip_with_existing_key(crypto: PiiCrypto) -> None:
    user_id = uuid.uuid4()
    dek = crypto.generate_dek()
    row = UserEncryptionKeyModel(user_id=user_id, dek_wrapped=crypto.wrap_dek(dek))
    session = _FakeSession({user_id: row})
    enc = PiiFieldEncryptor(crypto, DekResolver(crypto))

    stored = await enc.encrypt(session, user_id, "본문")  # type: ignore[arg-type]
    assert await enc.decrypt(session, user_id, stored) == "본문"  # type: ignore[arg-type]
    assert await enc.encrypt_opt(session, user_id, None) is None  # type: ignore[arg-type]
    assert await enc.decrypt_opt(session, user_id, None) is None  # type: ignore[arg-type]
