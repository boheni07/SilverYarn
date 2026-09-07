"""Device 도메인 엔티티 — schema.md §5 `devices` 테이블 매핑.

설치모드 판별 임계값(decisions.md #5, 확정 — 임의 변경 금지):
  RAM < 6GB 또는 Android <= 11 (API 30) → kiosk, 그 외 normal.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

KIOSK_RAM_THRESHOLD_GB = Decimal("6.0")
KIOSK_ANDROID_MAX_VERSION = 11


class InstallMode(StrEnum):
    KIOSK = "kiosk"
    NORMAL = "normal"


def determine_install_mode(ram_gb: Decimal, android_version: str) -> InstallMode:
    """decisions.md #5 — 보수적 판정(둘 중 하나라도 미달 시 키오스크).

    ⚠️ android_version은 문자열(예: "9", "11", "13")로 저장되므로 사전식 비교(<=)를
    쓰면 "9" <= "11"이 False로 잘못 평가된다(문자 '9' > '1'). 반드시 정수로 변환해
    비교한다 — 메이저 버전만 온다는 전제(마이너 버전 포함 시 파싱 로직 확장 필요).
    """
    major_version = int(android_version.split(".")[0])
    if ram_gb < KIOSK_RAM_THRESHOLD_GB or major_version <= KIOSK_ANDROID_MAX_VERSION:
        return InstallMode.KIOSK
    return InstallMode.NORMAL


@dataclass
class Device:
    id: UUID
    display_id: str
    model_name: str | None
    user_id: UUID
    ram_gb: Decimal
    android_version: str
    install_mode: InstallMode
    ai_tops: Decimal | None
    slm_model_version: str | None  # schema.md v1.3, decisions.md #35
    prompt_pack_version: str | None  # schema.md v1.3, decisions.md #35
    installed_at: datetime
    last_sync_at: datetime | None
