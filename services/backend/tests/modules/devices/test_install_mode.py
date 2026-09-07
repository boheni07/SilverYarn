"""decisions.md #5 설치모드 판별 임계값 — 순수 도메인 로직 테스트 (RAM<6GB 또는 Android<=11 → kiosk)."""

from decimal import Decimal

import pytest

from core_service.modules.devices.domain.device import InstallMode, determine_install_mode


@pytest.mark.parametrize(
    ("ram_gb", "android_version", "expected"),
    [
        (Decimal("4.0"), "13", InstallMode.KIOSK),  # RAM 미달만
        (Decimal("8.0"), "10", InstallMode.KIOSK),  # Android 버전 미달만
        (Decimal("3.0"), "9", InstallMode.KIOSK),  # 둘 다 미달
        (Decimal("8.0"), "13", InstallMode.NORMAL),  # 둘 다 충족
        (Decimal("6.0"), "12", InstallMode.NORMAL),  # 경계값(6GB 미만 아님, 11 초과)
    ],
)
def test_determine_install_mode(ram_gb, android_version, expected) -> None:
    assert determine_install_mode(ram_gb, android_version) == expected
