#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "robostudio") not in sys.path:
    sys.path.insert(0, str(ROOT / "robostudio"))

from robostudio.domain.device_registry import DeviceRegistry
from robostudio.domain.hardware_build_matrix import HardwareBuildMatrix
from robostudio.domain.hardware_config import HardwareConfig
from robostudio.domain.hardware_macro_generator import HardwareMacroGenerator
from tools.hardware_feature_config import macro_name

BOARD = ROOT / "robot-platform/main/src/HardwareAbstraction/BoardProfile.h"

REQUIRED_V2_FEATURES = ("line_sensor", "encoder", "servo", "imu", "buzzer")


def macro_value(header: str, device_id: str) -> int:
    macro = macro_name(device_id)
    for line in header.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == "#define" and parts[1] == macro:
            return int(parts[2])
    raise AssertionError(f"missing macro for {device_id}: {macro}")


def test_existing_full_matrix_stays_green() -> None:
    result = HardwareBuildMatrix.verify()
    assert result.passed, "\n".join(result.failures)


def test_required_v2_features_have_on_off_cases() -> None:
    ids = set(DeviceRegistry.ids())
    for device_id in REQUIRED_V2_FEATURES:
        assert device_id in ids, f"required V2 feature not registered: {device_id}"

    cases = HardwareBuildMatrix.cases()
    for device_id in REQUIRED_V2_FEATURES:
        states = {case.enabled for case in cases if case.device_id == device_id}
        assert states == {False, True}, (device_id, states)


def test_toggle_changes_only_selected_capability_macro() -> None:
    generator = HardwareMacroGenerator()
    baseline = HardwareConfig.create_default()

    for device_id in REQUIRED_V2_FEATURES:
        off = HardwareConfig.from_dict(baseline.to_dict())
        on = HardwareConfig.from_dict(baseline.to_dict())
        off.set_enabled(device_id, False)
        on.set_enabled(device_id, True)

        off_header = generator.render(off)
        on_header = generator.render(on)

        assert macro_value(off_header, device_id) == 0
        assert macro_value(on_header, device_id) == 1

        for other in DeviceRegistry.ids():
            if other == device_id:
                continue
            assert macro_value(off_header, other) == macro_value(on_header, other), (
                device_id,
                other,
            )

        # Generated capability headers must never contain physical wiring.
        for text in (off_header, on_header):
            for forbidden in (
                "GPIO",
                "MOTOR_SAFE_EN",
                "SYSTEM_I2C",
                "MCP23017",
                "SERVO1",
                "SERVO2",
                "ENCODER_L_A",
                "ENCODER_R_B",
                "LINE_FAR_LEFT",
                "BUZZER_CTRL",
            ):
                assert forbidden not in text, (device_id, forbidden)


def test_board_profile_is_fixed_and_independent_from_feature_state() -> None:
    board_before = BOARD.read_text(encoding="utf-8")
    generator = HardwareMacroGenerator()

    for device_id in REQUIRED_V2_FEATURES:
        for enabled in (False, True):
            cfg = HardwareConfig.create_default()
            cfg.set_enabled(device_id, enabled)
            generator.render(cfg)
            assert BOARD.read_text(encoding="utf-8") == board_before

    required_physical_contract = (
        "MOTOR_SAFE_EN = 4",
        "SYSTEM_I2C_SCL = 13",
        "SYSTEM_I2C_SDA = 21",
        "SERVO1 = 16",
        "SERVO2 = 17",
        "ENCODER_L_A = 34",
        "ENCODER_L_B = 35",
        "ENCODER_R_A = 36",
        "ENCODER_R_B = 39",
        "ADDRESS = 0x20",
        "LINE_FAR_LEFT = 0",
        "LINE_LEFT = 1",
        "LINE_CENTER = 2",
        "LINE_RIGHT = 3",
        "LINE_FAR_RIGHT = 4",
        "LED_LEFT = 0",
        "LED_RIGHT = 1",
        "BUZZER_CTRL = 2",
    )
    for token in required_physical_contract:
        assert token in board_before, token


def test_display_is_optional_not_silently_invented() -> None:
    ids = set(DeviceRegistry.ids())
    # TEST-008 says Display ON/OFF only if introduced. No selectable display
    # capability exists yet because V2-HLT-005 is blocked on the OLED hardware contract.
    assert "display" not in ids
    assert "oled" not in ids


def main() -> int:
    test_existing_full_matrix_stays_green()
    print("PASS: existing H25-G full hardware ON/OFF matrix remains green")
    test_required_v2_features_have_on_off_cases()
    print("PASS: Line/Encoder/Servo/IMU/Buzzer all have explicit ON and OFF cases")
    test_toggle_changes_only_selected_capability_macro()
    print("PASS: each V2 toggle changes only its capability macro")
    test_board_profile_is_fixed_and_independent_from_feature_state()
    print("PASS: feature toggles cannot remap BoardProfile or MCP allocation")
    test_display_is_optional_not_silently_invented()
    print("PASS: optional Display matrix is deferred until an OLED capability is introduced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
